#!/usr/bin/env python3
import timeio.feta
from timeio.feta import *
from timeio.feta import _prop, _create, _fetch

# hack: overwrite config_db with TMM-DB for all classes in feta
#   only do this for testing/debugging
#   DO NOT DO THIS IN PRODUCTION CODE !!
for x in [
    Project,
    IngestType,
    S3Store,
    MQTT,
    MQTTDeviceType,
    ExtSFTP,
    ExtAPI,
    ExtAPIType,
    FileParser,
    FileParserType,
    QAQCTest,
    QAQC,
]:
    x._schema = "thing_management_db"

# print(Project._schema)


class PropExample:
    def __init__(self):
        self._attrs = {"name": "foo"}

    # All three versions (name1, name2, name3) are identical, see -> show_example()

    # _prop is just syntactic sugar for property and to accept typehints
    name1 = _prop(lambda self: self._attrs["name"])

    name2 = property(lambda self: self._attrs["name"])

    @property
    def name3(self):
        return self._attrs["name"]


def show_example():
    pex = PropExample()
    print(pex.name1)
    print(pex.name2)
    print(pex.name3)
    assert pex.name1 == pex.name2 == pex.name3


class ThingWIP(Base, FromNameMixin, FromUUIDMixin):
    _schema = "thing_management_db"
    _table_name = "thing"

    # [1]
    # To protect values put them in _protected_values, which means they get masked
    # '*****' if the class is logged or printed.
    # TO see it in real live, check feta.Database._protected_values
    _protected_values = frozenset({})

    # [2]
    # These properties are the same in the config DB as in the new TMM FE,
    # so we need no change
    id: int = _prop(lambda self: self._attrs["id"])
    uuid = _prop(lambda self: str(self._attrs["uuid"]))
    name = _prop(lambda self: self._attrs["name"])
    description: str | None = _prop(lambda self: self._attrs["description"])
    project_id: int = _prop(lambda self: self._attrs["project_id"])
    ingest_type_id: int = _prop(lambda self: self._attrs["ingest_type_id"])

    # [3]
    # we add some NEW fields that are ONLY in the TMM FE
    created_at = _prop(lambda self: self._attrs["created_at"])
    created_by = _prop(lambda self: self._attrs["created_by"])

    # [4]
    # These properties are ONLY present in the old FE,
    # so we need some more complex logic / queries to get the same result
    ext_sftp_id: int | None = _fetch(f"select x.id from {_schema}.external_sftp_ingest x left join {_schema}.thing t on t.id = x.thing_id where t.uuid::text = %s", "uuid", "id")  # fmt: skip
    ext_api_id: int | None = _fetch(f"select x.id from {_schema}.external_api_ingest x left join {_schema}.thing t on t.id = x.thing_id where t.uuid::text = %s", "uuid", "id")  # fmt: skip
    s3_store_id: int | None = _fetch(f"select x.id from {_schema}.rawdatastorage x left join {_schema}.thing t on t.id = x.thing_id where t.uuid::text = %s", "uuid", "id")  # fmt: skip
    mqtt_id: int | None = _fetch(f"select x.id from {_schema}.mqtt_ingest x left join {_schema}.thing t on t.id = x.thing_id where t.uuid::text = %s", "uuid", "id")  # fmt: skip

    # [5]
    # Here we need no change, because we create the feta objects from the id (see [4] above)
    # Note: if the something_id is None, we also get None instead of the object.
    # For example if `thing.ext_sftp_id` is None then `thing.ext_sftp` is also None
    project: Project = _create(Project, f"select * from {_schema}.project where id = %s", "project_id")  # fmt: skip
    ingest_type: IngestType = _create(IngestType, f"select * from {_schema}.ingest_type where id = %s", "ingest_type_id")  # fmt: skip
    s3_store: S3Store | None = _create(S3Store, f"select * from {_schema}.s3_store where id = %s", "s3_store_id")  # fmt: skip
    mqtt: MQTT = _create(MQTT, f"select * from {_schema}.mqtt_ingest where id = %s", "mqtt_id")  # fmt: skip
    ext_sftp: ExtSFTP | None = _create(ExtSFTP, f"select * from {_schema}.ext_sftp where id = %s", "ext_sftp_id")  # fmt: skip
    ext_api: ExtAPI | None = _create(ExtAPI, f"select * from {_schema}.ext_api where id = %s", "ext_api_id")  # fmt: skip
    legacy_qaqc_id: int | None = _prop(lambda self: self._attrs.get("legacy_qaqc_id"))

    # [6]
    # This is the old legacy thing.Thing interface (see src/timeio/thing.py)
    # from even before feta was implemented. The properties
    # uuid, name, project, description are already defined above,
    # we define the missing attributes to be compatible with the Thing in thing.py
    database: Database = _prop(lambda self: self.project.database)
    raw_data_storage = s3_store
    external_sftp = ext_sftp
    external_api = ext_api
    # Note that thing.properties are not supported anymore
    properties = None


# [7] General notes
# The Base class implements a __repr__ function with prints the class name
# with all DB fields its gets from the DB (Base._attr). This means even if
# we don't implement a property for a field, we see it if we print the class.
# Take for example the following ThingMini class, which does not implement
# any property; if we print it see [7] below it is identical to ThingWIP.
# We can access an "unknown" field always via instance._attr['field_name'],
# see [8]
class ThingMini(Base, FromNameMixin, FromUUIDMixin):
    _schema = "thing_management_db"
    _table_name = "thing"


if __name__ == "__main__":
    logging.basicConfig(level="INFO")

    # [0]
    # First create a thing in the TMM FE with
    # name: TestThing
    # ingest type: mqtt
    # then run this example
    dsn = "postgresql://postgres:postgres@localhost/postgres"
    try:
        thing = ThingWIP.from_name("TestThingx", dsn=dsn)
    except timeio.feta.ObjectNotFound as e:
        e.add_note(
            "Did you created a test thing in the TMM FE? No?\n"
            "Create a new Thing with\n"
            " - name: 'TestThing'\n"
            " - ingest_type: mqtt\n"
        )
        raise e

    print("[1] Database.password and Database.ro_passwort are protected")
    print(thing.database)
    print()

    print("[2] Same DB fields for thing in configDB and TMM DB")
    print(thing.id)
    print(thing.uuid)
    print(thing.name)
    print(thing.description)
    print(thing.project_id)
    print()

    print("[3] Fields that only exist in TMM DB")
    print(thing.created_at)
    print(thing.created_by)
    print()

    print(
        "[4] We use complexer queries to get the fields that are only present in the\n"
        "configDB and which are NOT native fields in the thing table in the FE DB.\n"
        "Note that because we have a mqtt-thing the other values are None"
    )
    print(thing.ext_sftp_id)
    print(thing.ext_api_id)
    print(thing.s3_store_id)
    print(thing.mqtt_id)
    print()

    print("[5] Created objects from the ids above")
    print(thing.project)
    print(thing.ingest_type)
    print(thing.s3_store)
    print(thing.mqtt)
    print(thing.ext_sftp)
    print(thing.ext_api)
    print(thing.legacy_qaqc_id)
    print()

    print("[6] legacy thing.Thing (src/timeio/thing.py) interface")
    print(thing.database)
    print(thing.raw_data_storage)
    print(thing.external_sftp)
    print(thing.external_api)
    print(thing.properties)
    print()

    print(
        "[7] The repr of a feta object always prints the FetaObj._attr, \n"
        "not the implemented attributes of the class. The _attrs are all fields\n"
        "we get from the DB with 'select * from object_table where id = ...'"
    )
    thing_mini = ThingMini.from_name("TestThing", dsn=dsn)
    print(thing_mini)
    print(thing)
    print()

    print(
        "[8] Access via `FetaObject._attr['field_name']`, but this is not very "
        "convenient. That's why we add properties, which also enable auto-completion"
        "on all/most modern IDEs and python editors."
    )
    print(thing_mini._attrs["project_id"])
    print(thing.project_id)
