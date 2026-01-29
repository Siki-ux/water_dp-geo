#!/usr/bin/env python3

import sys
import os
import logging
import click

from dotenv import dotenv_values


def get_dotenv_vars(path: str) -> list:
    """Reads all keys of an .env file into a list"""
    env_vars = dotenv_values(path)
    env_vars_list = [k for k, _ in env_vars.items()]
    return env_vars_list


@click.command()
@click.argument("check_dotenv_path")
@click.argument("lookup_dotenv_path")
def main(check_dotenv_path: str, lookup_dotenv_path: str):
    """
    Compares the keys of two .env files.

    Parameters:
        check_dotenv_path (str): path to .env file with variables
         that are checked to see if they appear in the lookup file
        lookup_dotenv_path (str): path to lookup .env file

    If any variables of the check file are missing in the lookup file,
    the script exits with code 1.
    """
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    check_envvars = get_dotenv_vars(check_dotenv_path)
    lookup_envvars = get_dotenv_vars(lookup_dotenv_path)
    missing_in_lookup_file = set(lookup_envvars) - set(check_envvars)

    if not missing_in_lookup_file:
        logging.info("No missing envvars in checked .env file")
        sys.exit(0)
    else:
        logging.error(
            f"The following envvars are not in the checked .env file:\n{missing_in_lookup_file}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
