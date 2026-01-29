import os
import sys

import psycopg
from psycopg.rows import dict_row

INSERT_QUERY = """
        INSERT INTO public.schema_thing_mapping (schema, thing_uuid)
        VALUES (%(schema_name)s, %(thing_uuid)s)
        """


def get_schemas_with_things(cur):
    return cur.execute(
        """SELECT schemaname FROM pg_tables
           WHERE tablename = 'thing';"""
    ).fetchall()


def get_things(cur, schema):
    return cur.execute(f"""SELECT uuid::varchar from {schema}.thing;""").fetchall()


def get_schema_thing_dict(cur):
    schemas_things_dict = list()
    schemas = get_schemas_with_things(cur)
    for schema in schemas:
        things = get_things(cur, schema["schemaname"])
        for thing in things:
            schemas_things_dict.append(
                {"schema_name": schema["schemaname"], "thing_uuid": thing["uuid"]}
            )
    return schemas_things_dict


usage = f"""{os.path.basename(__file__)} DB_URL

Maps things to the related schema/datasource of existing schemas and things
and inserts it into the public.schema_thing_mapping table.

    DB_URL is the connection string of the respective database
    
Example:
    DB_URL=postgresql://postgres:postgres@localhost:5432/postgres
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)

    with psycopg.connect(sys.argv[1]) as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            schemas_things = get_schema_thing_dict(cursor)
            cursor.executemany(INSERT_QUERY, schemas_things)
    print("Data inserted successfully")
