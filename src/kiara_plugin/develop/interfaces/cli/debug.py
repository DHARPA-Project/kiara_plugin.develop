# -*- coding: utf-8 -*-

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)


import rich_click as click
from kiara.context import Kiara
from kiara.utils.cli import terminal_print_model


@click.group("debug")
@click.pass_context
def debug(ctx):
    """Kiara context related sub-commands."""


@debug.command("print-jobs")
@click.pass_context
def print_jobs(ctx):
    """Print stored jobs."""

    kiara: Kiara = ctx.obj["kiara"]

    all_records = kiara.job_registry.retrieve_all_job_records()

    terminal_print_model(*all_records.values())
