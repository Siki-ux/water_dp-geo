# python
import pytest
import uuid
import random

from unittest.mock import MagicMock
from crontab import CronItem

from setup_crontab import CreateThingInCrontabHandler


class ProjectMock:
    def __init__(self, name):
        self.name = name


def ThingMock(**overrides):
    _base_attrs = {
        "uuid": str(uuid.uuid4()),
        "name": "thing-name",
        "project": ProjectMock(name="project-name"),
        "ext_api": None,
        "ext_sftp": None,
    }
    thing = MagicMock()
    for k, v in _base_attrs.items():
        setattr(thing, k, v)
    for k, v in overrides.items():
        setattr(thing, k, v)
    return thing


@pytest.mark.parametrize(
    ["thing", "expected"],
    [
        (
            ThingMock(
                ext_sftp=MagicMock(
                    sync_interval=15, sync_enabled=True, uri="sftp://test:22"
                ),
            ),
            "sFTP sftp://test:22 @ 15m and schedule",
        ),
        (
            ThingMock(
                ext_api=MagicMock(
                    sync_interval=120, enabled=True, api_type_name="TestAPI"
                ),
            ),
            "TestAPI-API @ 120m and schedule",
        ),
        (ThingMock(ext_sftp=None, ext_api=None), ""),
    ],
)
def test_create_job(thing, expected):
    job = CronItem()
    info = CreateThingInCrontabHandler.apply_job(job, thing)
    assert info == expected or info.startswith(expected)


@pytest.mark.parametrize("uuid", ["000-001-99"])
@pytest.mark.parametrize(
    "typ, kwargs",
    [
        ("sftp", {"uri": "sftp://make:22"}),
        (
            "ext_api",
            {"api_type_name": "MakeAPI"},
        ),
    ],
)
@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("interval", [10, 1000, 10080])
def test_update_job_sftp(uuid, typ, kwargs, enabled, interval):
    if typ == "sftp":
        ext_sftp = MagicMock(**kwargs, sync_enabled=enabled, sync_interval=interval)
        thing = ThingMock(ext_sftp=ext_sftp, uuid=uuid)
    elif typ == "ext_api":
        ext_api = MagicMock(**kwargs, enabled=enabled, sync_interval=interval)
        thing = ThingMock(ext_api=ext_api, uuid=uuid)
    else:
        raise RuntimeError("wong test setup")
    job = CronItem()

    # create a job
    CreateThingInCrontabHandler.apply_job(job, thing)
    assert job.enabled == enabled
    assert uuid in job.comment
    assert uuid in job.command

    # call render() to actual create a copy (and convert to a string),
    # job.slices would be just a reference, that would update on job update.
    old_slices = job.slices.render()

    # we mock an external thing update ...
    if typ == "sftp":
        thing.ext_sftp.sync_enabled = not enabled
        thing.ext_sftp.sync_interval = 1717
    else:
        thing.ext_api.enabled = not enabled
        thing.ext_api.sync_interval = 1717

    # ... and update the job with the modified thing
    CreateThingInCrontabHandler.apply_job(job, thing, is_new=False)
    assert job.enabled == (not enabled)
    assert uuid in job.comment
    assert uuid in job.command

    # We just assert that a change in schedule happened, to test the explicit
    # update of the schedule/slices we have an extra test below
    assert job.slices.render() != old_slices


@pytest.mark.parametrize(
    "thing, expected",
    [
        (
            ThingMock(name="thing", uuid="uuid", project=ProjectMock("project")),
            "project | thing | uuid",
        )
    ],
)
def test_mk_comment(thing, expected):
    comment = CreateThingInCrontabHandler.mk_comment(thing)
    # remove the time as it is harder to check
    comment_chunk = " | ".join(comment.split(" | ")[1:])
    assert comment_chunk == expected


@pytest.mark.parametrize(
    "job, thing, expected",
    [
        (CronItem(comment="project | thing | 0001"), ThingMock(uuid="0001"), True),
        (CronItem(comment="project | thing | 0001"), ThingMock(uuid="0002"), False),
    ],
)
def test_job_belongs_to_thing(job, thing, expected):
    assert CreateThingInCrontabHandler.job_belongs_to_thing(job, thing) == expected


@pytest.mark.parametrize(
    "schedule, expected",
    [
        ("* * * * *", 1),
        ("*/2 * * * *", 2),
        ("0-59/3 * * * *", 3),
        ("19-59/20 * * * *", 20),
        ("20-59/30 * * * *", 30),
        ("30-59/37 * * * *", 60),
        ("30-59/40 * * * *", 60),
        ("0-59/40 * * * *", 40),
        ("58-59/59 * * * *", 60),
        ("11 */1 * * *", 60),
        ("5 */2 * * *", 120),
        ("1 5 */1 * *", 1440),
        ("1 5 */2 * *", 2880),
        # tricky values
        ("8-59/9 * * * *", 9),  # [8,17,..,53],[8,17,.. -> 9,14,9 --> majority 9
        ("5-59/25 * * * *", 25),  # [5,30,55],[5,30,.. -> 25,10,25 --> majority: 25
        ("0-59/40 * * * *", 40),  # [0,40],[0,40].. -> 20,40,20 or 40,20,40 --> max: 40
        ("0-59/35 * * * *", 35),  # [0,35],[0,35].. -> 35,25,35 or 25,35,25 --> max: 35
    ],
)
def test_get_current_interval(schedule, expected):
    job = CronItem()
    job.setall(schedule)
    interval = CreateThingInCrontabHandler.get_current_interval(job)
    assert interval == expected


@pytest.mark.parametrize(
    ("schedule", "expected_base_minute"),
    [
        ("0 * * * *", 0),
        ("*/12 * * * *", 0),
        ("@daily", 0),
        ("10,30,50 * * * *", 10),
        ("7-59/12 3-23/5 * * *", 7),
        ("*/12,3-23/5 * * * *", 0),
        ("3-4/12,3-23/5 * * * *", 3),
    ],
)
def test_extract_base_minute(schedule, expected_base_minute):
    job = CronItem()
    job.setall(schedule)
    base_minute = CreateThingInCrontabHandler.extract_base_minute(job.slices)
    assert base_minute == expected_base_minute


@pytest.mark.parametrize(
    ("schedule", "expected_base_hour"),
    [
        ("* 0 * * *", 0),
        ("* */12 * * *", 0),
        ("@daily", 0),
        ("* 10,15,20 * * *", 10),
        ("* 7-23/12 * * *", 7),
        ("* */12,3-23/5 * * *", 0),
        ("* 3-4/12,3-23/5 * * *", 3),
    ],
)
def test_extract_base_hour(schedule, expected_base_hour):
    job = CronItem()
    job.setall(schedule)
    base_hour = CreateThingInCrontabHandler.extract_base_hour(job.slices)
    assert base_hour == expected_base_hour


@pytest.mark.parametrize(
    ("interval", "expected"),
    [
        # all following params need random.seed(42)
        (0, "0-59/1 * * * *"),
        (1, "0-59/1 * * * *"),
        (60, "40 0-23/1 * * *"),
        (60 * 24, "40 3 1-31/1 * *"),
        (60 * 24 * 7, "40 3 * * 0"),
        # other
        (30, "20-59/30 * * * *"),
        (120, "40 0-23/2 * * *"),
        (1440, "40 3 1-31/1 * *"),
        (10, "1-59/10 * * * *"),
        (360, "40 0-23/6 * * *"),
        (1500, "40 3 1-31/1 * *"),
        # minute adjustment: odd values get adjusted to the next lower
        # proper divisor of 60
        (17, "10-59/15 * * * *"),
        (19, "10-59/15 * * * *"),
        (11, "1-59/10 * * * *"),
        (7, "5-59/6 * * * *"),
        (8, "5-59/6 * * * *"),
        (31, "20-59/30 * * * *"),
        (32, "20-59/30 * * * *"),
        (45, "20-59/30 * * * *"),
        (55, "20-59/30 * * * *"),
        # hour adjustment: 1,2,3,4,6,8,12
        (122, "40 0-23/2 * * *"),
        (60 * 5, "40 0-23/4 * * *"),
        (60 * 7, "40 0-23/6 * * *"),
        (60 * 9, "40 0-23/8 * * *"),
        (60 * 10, "40 0-23/8 * * *"),
        (60 * 11, "40 0-23/8 * * *"),
        (60 * 14, "40 0-23/12 * * *"),
        (60 * 17, "40 0-23/12 * * *"),
        (60 * 20, "40 0-23/12 * * *"),
        (60 * 23, "40 0-23/12 * * *"),
        (1439, "40 0-23/12 * * *"),
        # week adjustment
        (10085, "40 3 * * 0"),
    ],
)
def test_new_schedule(interval, expected):
    # make random deterministic to ensure we always have the same test results
    random.seed(42)

    schedule = CreateThingInCrontabHandler.new_schedule(interval)
    schedule2 = CreateThingInCrontabHandler.new_schedule(interval)
    assert schedule == expected
    if interval in [0, 1]:
        return
    assert schedule != schedule2


@pytest.mark.parametrize(
    ("schedule", "new_interval", "expected"),
    [
        # base minute < 60
        ("0-59/5 * * * *", 10, "0-59/10 * * * *"),
        ("0-59/10 * * * *", 5, "0-59/5 * * * *"),
        ("*/15 * * * *", 30, "0-59/30 * * * *"),
        ("5-59/15 * * * *", 30, "5-59/30 * * * *"),
        # base minute >= new interval -> creates a new random base minute
        ("20-59/30 * * * *", 15, "10-59/15 * * * *"),  # needs random.seed(42)
        # 60 < new interval < 1440
        ("16 */4 * * *", 120, "16 */2 * * *"),
        ("16 0-23/4 * * *", 120, "16 */2 * * *"),
        ("16 */4 * * *", 121, "16 */2 * * *"),
        ("16 */4 * * *", 122, "16 */2 * * *"),
        ("16 */4 * * *", 179, "16 */2 * * *"),
        ("16 */4 * * *", 180, "16 */3 * * *"),
        # interval > 1440 (1day) and interval != 10080 (7days)
        ("37 5 */2 * *", 1440, "37 5 */1 * *"),
        ("37 5 * * *", 7200, "37 5 */5 * *"),
        ("37 5 * * *", 7201, "37 5 */5 * *"),
        ("37 5 * * *", 18719, "37 5 */12 * *"),
        ("37 5 * * *", 18720, "37 5 */13 * *"),
        ("37 5 * * *", 19000, "37 5 */13 * *"),
        ("37 5 * * *", 20000, "37 5 */13 * *"),
        ("37 5 * * *", 20160, "37 5 */14 * *"),
        # interval == 10080 (7days) -> uses a random weekday
        ("37 5 * * *", 10080, "37 5 * * 5"),  # needs random.seed(42)
        ("37 5 * * *", 10090, "37 5 * * 5"),  # needs random.seed(42)
        # no changes expected
        ("5,15,25,35,45,55 * * * *", 10, "5,15,25,35,45,55 * * * *"),
        ("16 */2 * * *", 120, "16 */2 * * *"),
        ("30 */6 * * *", 360, "30 */6 * * *"),
        ("37 5 */13 * *", 20000, "37 5 */13 * *"),
        ("37 5 */13 * *", 20001, "37 5 */13 * *"),
        ("56 15 * * 2", 10080, "56 15 * * 2"),
    ],
)
def test_update_cron_expression(schedule, new_interval, expected):
    # make random deterministic to ensure we always have the same test results
    random.seed(42)

    job = CronItem()
    job.setall(schedule)
    new_schedule = CreateThingInCrontabHandler.update_cron_expression(job, new_interval)
    assert new_schedule == expected
