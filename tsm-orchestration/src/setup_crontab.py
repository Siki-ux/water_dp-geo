from __future__ import annotations

import logging
from datetime import datetime
from random import randint

from crontab import CronItem, CronTab, CronRange, CronSlices

from timeio.mqtt import AbstractHandler, MQTTMessage
from timeio.feta import Thing
from timeio.common import get_envvar, setup_logging
from timeio.journaling import Journal
from timeio.typehints import MqttPayload

logger = logging.getLogger("crontab-setup")
journal = Journal("Cron")

MINUTES_PER_HOUR = 60
MINUTES_PER_DAY = 60 * 24
MINUTES_PER_WEEK = 60 * 24 * 7


class CreateThingInCrontabHandler(AbstractHandler):
    def __init__(self):
        super().__init__(
            topic=get_envvar("TOPIC"),
            mqtt_broker=get_envvar("MQTT_BROKER"),
            mqtt_user=get_envvar("MQTT_USER"),
            mqtt_password=get_envvar("MQTT_PASSWORD"),
            mqtt_client_id=get_envvar("MQTT_CLIENT_ID"),
            mqtt_qos=get_envvar("MQTT_QOS", cast_to=int),
            mqtt_clean_session=get_envvar("MQTT_CLEAN_SESSION", cast_to=bool),
        )
        self.tabfile = "/tmp/cron/crontab.txt"
        self.configdb_dsn = get_envvar("CONFIGDB_DSN")

    def act(self, content: MqttPayload.ConfigDBUpdate, message: MQTTMessage):
        thing = Thing.from_uuid(content["thing"], dsn=self.configdb_dsn)
        with CronTab(tabfile=self.tabfile) as crontab:
            for job in crontab:
                if self.job_belongs_to_thing(job, thing):
                    logger.info(f"Updating cronjob for thing {thing.name}")
                    info = self.apply_job(job, thing, is_new=False)
                    journal.info(f"Updated cronjob to sync {info}", thing.uuid)
                    return
            # if no job was found, create a new one
            job = crontab.new()
            logger.info(f"Creating job for thing {thing.name}")
            info = self.apply_job(job, thing, is_new=True)
            if not info:
                logger.warning(
                    "no Cronjob was created, because neither extAPI, "
                    "nor extSFTP is present"
                )
                return
            crontab.append(job)
            journal.info(f"Created cronjob to sync {info}", thing.uuid)

    @classmethod
    def apply_job(cls, job: CronItem, thing: Thing, is_new: bool = True) -> str:
        """Create or update a cron job for `thing`.
        If `is_new` is True the schedule is generated with `get_schedule`,
        otherwise it is adapted with `update_cron_expression`.
        Returns info string (or empty if nothing to do).
        """
        comment = cls.mk_comment(thing)
        uuid = thing.uuid
        script = "/scripts/mqtt_sync_wrapper.py"
        command = f"python3 {script} sync-thing {uuid} > $STDOUT 2> $STDERR"
        if thing.ext_sftp:
            interval = int(thing.ext_sftp.sync_interval)
            schedule = (
                cls.new_schedule(interval)
                if is_new
                else cls.update_cron_expression(job, interval)
            )
            job.enable(enabled=thing.ext_sftp.sync_enabled)
            info = f"sFTP {thing.ext_sftp.uri} @ {interval}m and schedule {schedule}"
        elif thing.ext_api:
            interval = int(thing.ext_api.sync_interval)
            schedule = (
                cls.new_schedule(interval)
                if is_new
                else cls.update_cron_expression(job, interval)
            )
            job.enable(enabled=thing.ext_api.enabled)
            info = f"{thing.ext_api.api_type_name}-API @ {interval}m and schedule {schedule}"
        else:
            return ""
        job.set_comment(comment, pre_comment=True)
        job.set_command(command)
        job.setall(schedule)
        return info

    @staticmethod
    def job_belongs_to_thing(job: CronItem, thing: Thing) -> bool:
        """Check if job belongs to thing."""
        return job.comment.split(" | ")[-1] == thing.uuid

    @staticmethod
    def mk_comment(thing: Thing) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"{now_str} | {thing.project.name} | {thing.name} | {thing.uuid}"

    @staticmethod
    def new_base_minute(interval: int) -> int:
        if interval == 0:
            return 0
        if 30 < interval < 60:
            # If for example the interval is 40min, we need to ensure
            # it can run twice an hour and therefor the start minute
            # must be lower than 20.
            return randint(0, 60 % interval - 1)
        return randint(0, min(interval - 1, 59))

    @staticmethod
    def new_base_hour(interval: int) -> int:
        if interval < MINUTES_PER_HOUR:
            return 0
        return randint(0, min(interval // MINUTES_PER_HOUR - 1, 23))

    @staticmethod
    def new_base_dom(interval: int) -> int:
        if interval < 2 * MINUTES_PER_DAY:
            return 1
        return randint(1, min(interval // MINUTES_PER_DAY - 1, 28))

    @classmethod
    def new_schedule(cls, interval: int) -> str:
        """Creates a new schedule with a random start point to avoid that
        all jobs run at the same time.
        """
        interval = cls.adjust_interval(_orig := interval)
        if _orig != interval:
            logger.info(f"adjusted interval form {_orig} minutes to {interval} minutes")

        start_m = cls.new_base_minute(interval)
        if interval < MINUTES_PER_HOUR:
            step_m = interval
            return f"{start_m}-59/{step_m} * * * *"

        start_h = cls.new_base_hour(interval)
        if interval < MINUTES_PER_DAY:
            start_h = cls.new_base_hour(interval)
            step_h = interval // MINUTES_PER_HOUR
            return f"{start_m} {start_h}-23/{step_h} * * *"

        elif interval == MINUTES_PER_WEEK:
            day_of_week = randint(0, 6)
            return f"{start_m} {start_h} * * {day_of_week}"

        # interval is larger than a day but not weekly
        else:
            start_dom = cls.new_base_dom(interval)
            step_day = interval // MINUTES_PER_DAY
            return f"{start_m} {start_h} {start_dom}-31/{step_day} * *"

    @staticmethod
    def get_current_interval(job: CronItem) -> int:
        """Get interval in minutes from crontab.txt entry"""
        schedule = job.schedule(datetime(2020, 1, 1, 23, 59, 59))
        # avoid to have one value in the last hour and one in the next,
        # therefore we avoid schedule.get_prev()
        next_run = schedule.get_next()
        after_next_run = schedule.get_next()
        return int((after_next_run - next_run).total_seconds() / 60)

    @staticmethod
    def adjust_interval(interval: int) -> int:
        """Adjust the interval to a value we can process cleanly in a cron schedule."""
        if interval == 0:
            return 1

        # We adjust the interval to proper divisor of 60.
        if interval <= MINUTES_PER_HOUR:
            divisors = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60]
            return max(d for d in divisors if d <= interval)

        # We adjust the interval to an exact hourly value which
        # also is a proper divisor of 24h (1,2,3,4,6,8,12,24).
        elif interval <= MINUTES_PER_DAY:
            divisors = [60, 120, 180, 240, 360, 480, 720, 1440]
            return max(d for d in divisors if d <= interval)

        # We adjust the interval to exactly a 7-day value if it's close.
        elif MINUTES_PER_WEEK <= interval < MINUTES_PER_DAY * 8:
            return MINUTES_PER_WEEK

        # We adjust the interval to an exact daily value.
        return (interval // MINUTES_PER_DAY) * MINUTES_PER_DAY

    @staticmethod
    def extract_base_minute(slices: str | CronSlices) -> int | None:
        """Extract the minute value from the cron expression.
        Returns the first numeric start value.
        """
        if isinstance(slices, str):
            slices = CronSlices(slices)
        # if we have a list of expressions like 1,2,4-59/5
        # we extract the base minute only from the first one.
        minutes = slices[0].parts[0]
        if isinstance(minutes, int):
            return minutes
        assert isinstance(minutes, CronRange)
        return minutes.vfrom

    @staticmethod
    def extract_base_hour(slices: str | CronSlices) -> int | None:
        """Extract the hour value from the cron expression.
        Returns the first numeric start value.
        """
        if isinstance(slices, str):
            slices = CronSlices(slices)
        # If we have a list of expressions like 1,2,4-23/5
        # we extract the base hour only from the first one.
        hour = slices[1].parts[0]
        if isinstance(hour, int):
            return hour
        assert isinstance(hour, CronRange)
        return hour.vfrom

    @classmethod
    def update_cron_expression(cls, job, interval: int) -> str:
        """Update cron while keeping the same base minute for consistency.
        If the existing schedule already encodes the requested periodicity
        (produced by `get_schedule`, e.g. contains '/{step}', range-with-step
        or a matching comma-list for minutes), return the original string unchanged.
        """
        interval = cls.adjust_interval(_orig := interval)
        if _orig != interval:
            logger.info(f"adjusted interval form {_orig} minutes to {interval} minutes")

        current_interval = cls.get_current_interval(job)
        if current_interval == interval:
            return str(job.slices)

        base_minute = cls.extract_base_minute(job.slices)
        base_hour = cls.extract_base_hour(job.slices)

        if interval < MINUTES_PER_HOUR:
            if base_minute >= interval:
                base_minute = cls.new_base_minute(interval)
            return f"{base_minute}-59/{interval} * * * *"

        elif interval < MINUTES_PER_DAY:
            hour_step = interval // 60
            return f"{base_minute} */{hour_step} * * *"

        elif interval == MINUTES_PER_WEEK:
            dow = randint(0, 6)
            return f"{base_minute} {base_hour} * * {dow}"

        else:  # new_interval > DAY_MINUTES
            day_step = interval // (60 * 24)
            return f"{base_minute} {base_hour} */{day_step} * *"


if __name__ == "__main__":
    setup_logging(get_envvar("LOG_LEVEL", "INFO"))
    CreateThingInCrontabHandler().run_loop()
