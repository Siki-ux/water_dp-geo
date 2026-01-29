#!/usr/bin/env python3

from __future__ import annotations
import click
import os
import shutil
import psycopg

from psycopg import sql

from compare_datastreams import DatastreamComparer
from set_parser_duplicate_false import cleanup


@click.command()
@click.argument("schema", type=str)
@click.argument(
    "dsn", type=str, default="postgresql://postgres:postgres@localhost:5432/postgres"
)
@click.argument("frnt_schema", type=str, default="frontenddb")
@click.argument("cfg_schema", type=str, default="config_db")
def update_datastreams(schema: str, dsn: str, frnt_schema: str, cfg_schema: str):
    mapping_dirs = os.listdir("datastream_mapping")
    schema_folder = (
        os.path.join("datastream_mapping", f"{schema}")
        if schema in mapping_dirs
        else None
    )
    if not schema_folder:
        print(f"No matching folder found for {schema}")
        return False
    mapping_folder = os.path.join(schema_folder, "mappings")
    if not os.path.isdir(mapping_folder) or not os.listdir(mapping_folder):
        print(f"No mapping yamls found in '{mapping_folder}'")
        return False
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            drop_datastream_pos_constraint(cur, schema)
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                set_search_path(cur, schema)

                for mapping_file in os.listdir(mapping_folder):
                    mapping_path = os.path.join(mapping_folder, mapping_file)
                    comparer = DatastreamComparer(dsn, schema, mapping_path)
                    compare_result = comparer.compare_datastreams()
                    if any(not ds["equal"] for ds in compare_result["compare"]):
                        print("At least one datastream is unequal — skipping.")
                        with psycopg.connect(dsn, autocommit=True) as conn2:
                            with conn2.cursor() as cur2:
                                add_datastream_pos_constraint(cur2, schema)
                        return False
                    thing_uuid = compare_result["thing_uuid"]
                    ds_header_ids = []
                    print(f"Start processing datastreams for thing {thing_uuid}...")
                    for ds in compare_result["compare"]:
                        if ds["equal"]:
                            try:
                                print(
                                    f"Renaming datastream at position {ds['ds_position_id']} to {ds['ds_header_name']}"
                                )
                                rename_datastream(
                                    cur,
                                    thing_uuid,
                                    ds["ds_position_pos"],
                                    ds["ds_header_pos"],
                                )
                                ds_header_ids.append(ds["ds_header_id"])
                            except ValueError:
                                print(
                                    f"Datastream at position {ds['ds_position_id']} not found, skipping."
                                )
                    for ds_id in ds_header_ids:
                        delete_datastream_observations(cur, thing_uuid, ds_id)
                        delete_datastream(cur, thing_uuid, ds_id)
                    cleanup(thing_uuid, dsn, cfg_schema, frnt_schema)
                    move_yaml_to_done(mapping_path, schema_folder)
                set_search_path(cur, schema)
            conn.commit()
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                add_datastream_pos_constraint(cur, schema)

    except Exception as e:
        print(f"Error during processing. No changes were applied: {e}")
        conn.rollback()
        return False
    return True


def set_search_path(cur, schema: str) -> None:
    identifier = sql.Identifier(schema)
    query = sql.SQL("SET search_path TO {}").format(identifier)
    cur.execute(query)


def get_thing_name(cur, thing_uuid: str) -> str:
    query = sql.SQL("SELECT name FROM thing WHERE uuid = {thing_uuid}").format(
        thing_uuid=sql.Literal(thing_uuid)
    )
    cur.execute(query)
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(f"No thing found with UUID: {thing_uuid}")


def rename_datastream(cur, thing_uuid: str, ds_pos: int, ds_name: str) -> None:
    ## Drop the unique constraint temporarily
    # cur.execute(
    #    "ALTER TABLE datastream "
    #    "DROP CONSTRAINT IF EXISTS 'datastream_thing_id_position_9f2cfe68_uniq'"
    # )
    thing_name = get_thing_name(cur, thing_uuid)
    ds_name_new = f"{thing_name}/{ds_name}"
    ds_pos_new = ds_name

    query = sql.SQL(
        "UPDATE datastream d "
        "SET name = {name_new}, position = {pos_new} "
        "FROM thing t "
        "WHERE d.thing_id = t.id "
        "AND t.uuid = {thing_uuid} "
        "AND d.position = {pos_old}::text",
    ).format(
        name_new=sql.Literal(ds_name_new),
        pos_new=sql.Literal(ds_pos_new),
        thing_uuid=sql.Literal(thing_uuid),
        pos_old=sql.Literal(ds_pos),
    )
    print(query.as_string())
    cur.execute(query)


def delete_datastream_observations(cur, thing_uuid: str, ds_id: int) -> None:
    query = sql.SQL(
        "DELETE FROM observation o "
        "USING datastream d "
        "JOIN thing t ON d.thing_id = t.id "
        "WHERE o.datastream_id = d.id "
        "AND t.uuid = {thing_uuid} "
        "AND d.id = {ds_id}"
    ).format(
        thing_uuid=sql.Literal(thing_uuid),
        ds_id=sql.Literal(ds_id),
    )
    print(query.as_string())
    cur.execute(query)


def delete_datastream(cur, thing_uuid: str, ds_id: int) -> None:
    query = sql.SQL(
        "DELETE FROM datastream d "
        "USING thing t "
        "WHERE d.thing_id = t.id "
        "AND t.uuid = {thing_uuid} "
        "AND d.id = {ds_id}"
    ).format(
        thing_uuid=sql.Literal(thing_uuid),
        ds_id=sql.Literal(ds_id),
    )
    print(query.as_string())
    cur.execute(query)


def drop_datastream_pos_constraint(cur, schema) -> None:
    cur.execute(
        sql.SQL(
            "ALTER TABLE {schema}.datastream "
            "DROP CONSTRAINT IF EXISTS datastream_thing_id_position_9f2cfe68_uniq"
        ).format(schema=sql.Identifier(schema))
    )
    print("Dropped unique constraint on thing_id and position in datastream table.")


def add_datastream_pos_constraint(cur, schema) -> None:
    cur.execute(
        sql.SQL(
            "ALTER TABLE {schema}.datastream "
            "ADD CONSTRAINT datastream_thing_id_position_9f2cfe68_uniq "
            "UNIQUE (thing_id, position)"
        ).format(schema=sql.Identifier(schema))
    )
    print("Added unique constraint on thing_id and position in datastream table.")


def move_yaml_to_done(mapping_path, schema_folder):
    done_directory = os.path.join(schema_folder, "processed_mappings")
    try:
        os.makedirs(done_directory, exist_ok=True)
        filename = os.path.basename(mapping_path)
        destination_path = os.path.join(done_directory, filename)
        if os.path.exists(destination_path):
            os.remove(destination_path)
        shutil.move(mapping_path, done_directory)
        print(f"Moved '{mapping_path}' to '{done_directory}'")
    except Exception as e:
        print(f"Failed to move file: {e}")


# need to either rename new datastream or drop constraint on id, position before renaming
# need to get datastream_ids that should be deleted before renaming
#

if __name__ == "__main__":
    update_datastreams()
