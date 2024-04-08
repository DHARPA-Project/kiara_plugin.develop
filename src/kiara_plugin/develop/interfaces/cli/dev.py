# -*- coding: utf-8 -*-
import os

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)
import sys
import typing
from pathlib import Path

import rich_click as click

from kiara.utils.cli import output_format_option, terminal_print, terminal_print_model

if typing.TYPE_CHECKING:
    from kiara.api import Kiara
    from kiara.interfaces.python_api.base_api import BaseAPI


@click.group("dev")
@click.pass_context
def dev_group(ctx):
    """Kiara context related sub-commands."""


@dev_group.group("model")
@click.pass_context
def model(ctx):
    """Internal model related subcommands."""


@model.command("list")
@click.option(
    "--full-doc",
    "-d",
    is_flag=True,
    help="Display the full documentation for every module type (when using 'terminal' output format).",
)
@output_format_option()
@click.pass_context
def list_models(ctx, full_doc: bool, format: str):
    """List all available model types."""

    kiara: Kiara = ctx.obj.kiara

    registry = kiara.kiara_model_registry
    title = "All models"

    terminal_print_model(
        registry.all_models, format=format, in_panel=title, full_doc=full_doc
    )


@model.command(name="explain")
@click.argument("model_type_id", nargs=1, required=True)
@click.option("--schema", "-s", help="Display the model (json) schema.", is_flag=True)
@output_format_option()
@click.pass_context
def explain_module_type(ctx, model_type_id: str, format: str, schema: bool):
    """Print details of a model type."""

    from kiara.interfaces.python_api.models.info import KiaraModelTypeInfo

    kiara: Kiara = ctx.obj.kiara
    model_cls = kiara.kiara_model_registry.get_model_cls(kiara_model_id=model_type_id)
    info = KiaraModelTypeInfo.create_from_type_class(type_cls=model_cls, kiara=kiara)

    render_config = {"include_schema": schema}

    terminal_print_model(
        info,
        format=format,
        in_panel=f"Model type id: [b i]{model_type_id}[/b i]",
        **render_config,
    )


@model.group(name="subcomponents")
@click.pass_context
def subcomponents(ctx):
    """Display subcomponent for various model types."""


@subcomponents.command("operation")
@click.argument("operation_id", nargs=1, required=True)
@click.option(
    "--show-data",
    "-d",
    help="Whether to add nodes for the actual model data.",
    is_flag=True,
)
@click.pass_context
def print_operation_subcomponents(ctx, operation_id: str, show_data: bool):
    """Print the tree of a models subcomponents."""

    kiara_api: BaseAPI = ctx.obj.base_api

    operation = kiara_api.get_operation(operation=operation_id)
    tree = operation.create_renderable_tree(show_data=show_data)
    terminal_print(tree)


# @model.group(name="render")
# @click.pass_context
# def render(ctx):
#     """Code generator/Schema translator for kiara models.."""
#
#
# @render.command("typescript")
# @click.argument("filter", nargs=-1)
# @click.option(
#     "--output",
#     "-o",
#     help="The file to write the output, otherwise print to stdout.",
#     required=False,
# )
# @click.option("--force", "-f", help="Overwrite existing file(s)..", is_flag=True)
# @click.pass_context
# def render_typescript(
#     ctx,
#     filter: Tuple[str],
#     output: str,
#     force: bool,
# ):
#     """Create typescript models"""
#
#     from kiara_plugin.develop.schema.javascript import TypeScriptModelExporter
#
#     kiara = ctx.obj.kiara
#     exporter = TypeScriptModelExporter(kiara=kiara)
#
#     _output: Union[None, Path] = None
#     if output is not None:
#
#         _output = Path(output)
#         if _output.exists():
#             _output = _output / "kiara_models.ts"
#
#         if _output.exists():
#             if not force:
#                 terminal_print()
#                 terminal_print(
#                     f"Output file '{_output.as_posix()}' already exists: {_output} and '--force' not specified."
#                 )
#                 sys.exit(1)
#
#     translated = exporter.translate(filters=filter)
#     if _output is not None:
#         _output.write_text(translated["kiara_models.ts"])
#     else:
#         print(translated["kiara_models.ts"])
#
#
# @render.command("flatbuffers")
# @click.argument("filter", nargs=-1)
# @click.option(
#     "--output",
#     "-o",
#     help="The file to write the output, otherwise print to stdout.",
#     required=False,
# )
# @click.option("--force", "-f", help="Overwrite existing file(s)..", is_flag=True)
# @click.pass_context
# def render_flatbuffers(
#     ctx,
#     filter: Tuple[str],
#     output: str,
#     force: bool,
# ):
#     """Create flatbuffer schemas."""
#
#     from kiara_plugin.develop.schema.flatbuffers import FlatbuffersSchemaExporter
#
#     kiara = ctx.obj.kiara
#     exporter = FlatbuffersSchemaExporter(kiara=kiara)
#
#     _output: Union[None, Path] = None
#     if output is not None:
#
#         _output = Path(output)
#         if _output.exists():
#             _output = _output / "kiara_models.fbs"
#
#         if _output.exists():
#             if not force:
#                 terminal_print()
#                 terminal_print(
#                     f"Output file '{_output.as_posix()}' already exists: {_output} and '--force' not specified."
#                 )
#                 sys.exit(1)
#
#     translated = exporter.translate(filters=filter)
#     if _output is not None:
#         raise NotImplementedError()
#         # _output.write_text(translated["kiara_models.fbs"])
#     else:
#         for model, text in translated.items():
#             print("# ==========================================")
#             print(f"# {model}")
#             print(text)


@model.group(name="html")
@click.pass_context
def html(ctx):
    """Utilities to do html-related tasks with kiara models."""


@html.command("operation")
@click.argument("operation_id", nargs=1, required=True)
@click.option(
    "--show-data",
    "-d",
    help="Whether to add nodes for the actual model data.",
    is_flag=True,
)
@click.pass_context
def print_operation_subcomponents_html(ctx, operation_id: str, show_data: bool):
    """Print the tree of a models subcomponents."""

    kiara_api: BaseAPI = ctx.obj.base_api

    operation = kiara_api.get_operation(operation=operation_id)

    html = operation.create_html()
    print(html)


@dev_group.command("lineage-graph")
@click.argument("value", nargs=1)
@click.pass_context
def lineage_graph(ctx, value: str):
    """ "Print the lineage of a value as graph."""

    from kiara.utils.graphs import print_ascii_graph

    kiara_api: BaseAPI = ctx.obj.base_api

    _value = kiara_api.get_value(value)
    graph = _value.lineage.full_graph

    print_ascii_graph(graph)

@dev_group.group(name="testing")
@click.pass_context
def testing(ctx):
    """Utilities for testing-related tasks."""

@testing.command("create_archive")
@click.argument("job_desc", nargs=1)
@click.argument("target_archive", nargs=1)
@click.pass_context
def create_archive_for_tests(ctx, job_desc: str, target_archive: str):
    """Create a kiara archive with test data.

    Deletes any potential existing archive and archive spec file with the same name.
    """

    api: BaseAPI = ctx.obj.base_api

    target_archive_path = Path(target_archive)
    info_file = target_archive_path.parent / f"{target_archive_path.name}.json"

    if target_archive_path.exists():
        if not target_archive_path.name.endswith(".kiarchive"):
            terminal_print(
                f"Target archive '{target_archive}' exists and does not have a '.kiarchive' extension."
            )
            sys.exit(1)
        else:
            os.unlink(target_archive_path)

    if info_file.exists():
        os.unlink(info_file)

    job_desc = "/home/markus/projects/kiara/kiara_plugin.core_types/examples/jobs/logic_and_true.yaml"
    results = api.run_job(job_desc, comment="comment")

    stored = api.export_values(target_archive=target_archive_path, values=results)

    terminal_print_model(stored, in_panel="Exported values")

    info = api.retrieve_archive_info(target_archive_path)

    json = info.model_dump_json()

    info_file.write_text(json)

    terminal_print("Test data archive created.")
