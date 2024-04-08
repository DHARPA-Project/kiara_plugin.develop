# -*- coding: utf-8 -*-
import sys
import typing
import uuid

import rich_click as click
from rich.table import Table

from kiara.utils.cli import terminal_print, terminal_print_model

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)


if typing.TYPE_CHECKING:
    from kiara.api import Kiara


@click.group("debug")
@click.pass_context
def debug(ctx):
    """Kiara context related sub-commands."""


@debug.group("job")
@click.pass_context
def jobs(ctx):
    """Kiara job related sub-commands."""


@jobs.command("list")
@click.pass_context
def print_jobs(ctx):
    """Print stored jobs."""

    from kiara.interfaces.python_api.models.info import JobInfos

    kiara: Kiara = ctx.obj.kiara  # type: ignore

    all_records = kiara.job_registry.retrieve_all_job_records()

    # infos = {}
    # for job in all_records.values():
    #     job_info = JobInfo.create_from_instance(kiara=kiara, instance=job)
    #     infos[str(job_info.job_record.job_id)] = job_info


    all_infos = JobInfos.create_from_instances(kiara=kiara, instances={ str(k): v for k, v in all_records.items() })
    terminal_print_model(all_infos, in_panel="Jobs")

@jobs.command("explain")
@click.argument("job_id")
@click.pass_context
def explain_job(ctx, job_id: str):
    """Print details of a job."""

    from kiara.interfaces.python_api.models.info import JobInfo

    kiara: Kiara = ctx.obj.kiara  # type: ignore

    try:
        _job_id = uuid.UUID(job_id)
    except Exception:
        terminal_print()
        terminal_print("Invalid job id. Must be a valid UUID.")
        sys.exit(1)

    job = kiara.job_registry.get_job_record(_job_id)

    info = JobInfo.create_from_instance(kiara=kiara, instance=job)
    terminal_print_model(info, in_panel=f"Details for job: {job_id}")


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
