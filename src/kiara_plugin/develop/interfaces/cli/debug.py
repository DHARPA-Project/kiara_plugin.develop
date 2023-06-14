# -*- coding: utf-8 -*-
import typing

import rich_click as click
from rich.table import Table

from kiara.utils.cli import terminal_print_model

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)


if typing.TYPE_CHECKING:
    from kiara.api import Kiara


@click.group("debug")
@click.pass_context
def debug(ctx):
    """Kiara context related sub-commands."""


@debug.command("print-jobs")
@click.pass_context
def print_jobs(ctx):
    """Print stored jobs."""

    kiara: Kiara = ctx.obj.kiara  # type: ignore

    all_records = kiara.job_registry.retrieve_all_job_records()

    terminal_print_model(*all_records.values())


@debug.command("print-workflows")
@click.pass_context
def print_workflows(ctx):
    """Print stored workflows."""

    kiara: Kiara = ctx.obj.kiara  # type: ignore

    workflow_aliases = kiara.workflow_registry.workflow_aliases.keys()

    table = Table(show_header=True)
    table.add_column("workflow alias", style="i")
    table.add_column("details")
    for workflow_alias in workflow_aliases:
        details = kiara.workflow_registry.get_workflow(workflow_alias)
        print(details)
