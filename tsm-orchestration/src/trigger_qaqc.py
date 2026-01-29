#!/usr/bin/env python3

import os
import sys
import click
from timeio.mqtt import publish_single
from datetime import datetime, timedelta
import re
import json


def parser_interval(interval_str):
    match = re.match(r"^(\d+)\s*([smhd])$", interval_str)
    if not match:
        raise click.BadParameter("Interval must be in format '<number>' '<s|m|h|d>'")
    value, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    else:
        raise click.BadParameter(
            "Invalid time interval unit. Use 's', 'm', 'h', or 'd'."
        )


@click.command()
@click.help_option("--help", "-h")
@click.option(
    "--interval", required=True, help="Time interval (e.g., '5m', '1h', '1d')"
)
@click.option("--project-uuid", required=True, help="Project UUID")
@click.option("--qc-settings-name", required=True, help="QC Settings Name")
def main(interval, project_uuid, qc_settings_name):
    interval_td = parser_interval(interval)
    end_date = datetime.now().astimezone().replace(microsecond=0)
    start_date = end_date - interval_td

    payload = {
        "version": 2,
        "project_uuid": project_uuid,
        "qc_settings_name": qc_settings_name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    topic = os.getenv("TOPIC_DATA_PARSED", "data_parsed")
    json_payload = json.dumps(payload)
    publish_single(topic, json_payload)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        with click.Context(main) as ctx:
            click.echo(main.get_help(ctx))
        sys.exit(0)
    main()
