import psycopg
from psycopg import sql
import json


def cleanup(thing_uuid, dsn, cfg_schema, frnt_schema) -> None:
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            update_parser_front(cur, thing_uuid, frnt_schema)
            update_parser_cfg(cur, thing_uuid, cfg_schema)


def set_search_path(cur, schema: str) -> None:
    identifier = sql.Identifier(schema)
    query = sql.SQL("SET SEARCH_PATH TO {}").format(identifier)
    cur.execute(query)


def update_parser_front(cur, thing_uuid: str, front_schema: str) -> None:
    set_search_path(cur, front_schema)
    p_id = get_parser_id_front(cur, thing_uuid)
    params = get_parser_params_front(cur, p_id)
    set_duplicate_false_front(cur, p_id, params)


def update_parser_cfg(cur, thing_uuid: str, cfg_schema: str) -> None:
    set_search_path(cur, cfg_schema)
    p_id = get_parser_id_cfg(cur, thing_uuid)
    params = get_parser_params_cfg(cur, p_id)
    set_duplicate_false_cfg(cur, p_id, params)


def get_parser_id_front(cur, thing_uuid: str) -> int:
    cur.execute(
        "SELECT tp.parser_id FROM tsm_thing_parser tp "
        "JOIN tsm_thing t ON tp.thing_id = t.id "
        "WHERE t.thing_id = %s",
        (thing_uuid,),
    )
    return cur.fetchone()[0]  # Assuming file_parser_id is the first column


def get_parser_id_cfg(cur, thing_uuid: str) -> int:
    cur.execute(
        "SELECT s3.file_parser_id FROM s3_store s3 "
        "JOIN thing t ON s3.id = t.s3_store_id "
        "WHERE t.uuid = %s",
        (thing_uuid,),
    )
    return cur.fetchone()[0]  # Assuming file_parser_id is the first column


def get_parser_params_front(cur, parser_id: int) -> dict:
    cur.execute(
        "SELECT pandas_read_csv FROM tsm_csvparser WHERE parser_ptr_id = %s",
        (parser_id,),
    )
    return cur.fetchone()[0]  # Assuming pandas_read_csv is a JSON field


def get_parser_params_cfg(cur, parser_id: int) -> dict:
    cur.execute(
        "SELECT params FROM file_parser where id = %s",
        (parser_id,),
    )
    return cur.fetchone()[0]  # Assuming params is a JSON field


def set_duplicate_false_front(cur, parser_id: int, params: dict) -> None:
    if "duplicate" not in params:
        print("FrontendDB: No `duplicate` settings found, nothing to update...")
    elif params["duplicate"]:
        params["duplicate"] = False
        cur.execute(
            "UPDATE tsm_csvparser SET pandas_read_csv = %s WHERE parser_ptr_id = %s",
            (json.dumps(params), parser_id),
        )
        print("FrontendDB: `duplicate` set to false in tsm_csvparser.pandas_read_csv")
    else:
        print("FrontendDB: `duplicate` already set to false, nothing to update...")


def set_duplicate_false_cfg(cur, parser_id: int, params: dict) -> None:
    duplicate_setting = params.get("pandas_read_csv", {})
    if "duplicate" not in duplicate_setting:
        print("ConfigDB: No `duplicate` settings found, nothing to update...")
    elif duplicate_setting["duplicate"]:
        params["pandas_read_csv"]["duplicate"] = False
        cur.execute(
            "UPDATE file_parser SET params = %s WHERE id = %s",
            (json.dumps(params), parser_id),
        )
        print("ConfigDB: `duplicate` set to false in file_parser.params")
    else:
        print("ConfígDB: `duplicate` already set to false, nothing to update...")
