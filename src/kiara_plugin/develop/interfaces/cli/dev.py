# -*- coding: utf-8 -*-

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)
import sys
import typing
from pathlib import Path
from typing import Tuple, Union

import rich_click as click

from kiara.utils.cli import output_format_option, terminal_print, terminal_print_model

if typing.TYPE_CHECKING:
    from kiara.api import Kiara, KiaraAPI


@click.group("dev")
@click.pass_context
def dev_group(ctx):
    """Kiara context related sub-commands."""


@dev_group.group("model")
@click.pass_context
def model(ctx):
    pass


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

    kiara_api: KiaraAPI = ctx.obj.kiara_api

    operation = kiara_api.get_operation(operation=operation_id)
    tree = operation.create_renderable_tree(show_data=show_data)
    terminal_print(tree)


@model.group(name="render")
@click.pass_context
def render(ctx):
    """Code generator/Schema translator for kiara models.."""


@render.command("typescript")
@click.argument("filter", nargs=-1)
@click.option(
    "--output",
    "-o",
    help="The file to write the output, otherwise print to stdout.",
    required=False,
)
@click.option("--force", "-f", help="Overwrite existing file(s)..", is_flag=True)
@click.pass_context
def render_typescript(
    ctx,
    filter: Tuple[str],
    output: str,
    force: bool,
):
    """Create typescript models"""

    from kiara_plugin.develop.schema.javascript import TypeScriptModelExporter

    kiara = ctx.obj.kiara
    exporter = TypeScriptModelExporter(kiara=kiara)

    _output: Union[None, Path] = None
    if output is not None:

        _output = Path(output)
        if _output.exists():
            _output = _output / "kiara_models.ts"

        if _output.exists():
            if not force:
                terminal_print()
                terminal_print(
                    f"Output file '{_output.as_posix()}' already exists: {_output} and '--force' not specified."
                )
                sys.exit(1)

    translated = exporter.translate(filters=filter)
    if _output is not None:
        _output.write_text(translated["kiara_models.ts"])
    else:
        print(translated["kiara_models.ts"])


@render.command("flatbuffers")
@click.argument("filter", nargs=-1)
@click.option(
    "--output",
    "-o",
    help="The file to write the output, otherwise print to stdout.",
    required=False,
)
@click.option("--force", "-f", help="Overwrite existing file(s)..", is_flag=True)
@click.pass_context
def render_flatbuffers(
    ctx,
    filter: Tuple[str],
    output: str,
    force: bool,
):
    """Create flatbuffer schemas."""

    from kiara_plugin.develop.schema.flatbuffers import FlatbuffersSchemaExporter

    kiara = ctx.obj.kiara
    exporter = FlatbuffersSchemaExporter(kiara=kiara)

    _output: Union[None, Path] = None
    if output is not None:

        _output = Path(output)
        if _output.exists():
            _output = _output / "kiara_models.fbs"

        if _output.exists():
            if not force:
                terminal_print()
                terminal_print(
                    f"Output file '{_output.as_posix()}' already exists: {_output} and '--force' not specified."
                )
                sys.exit(1)

    translated = exporter.translate(filters=filter)
    if _output is not None:
        raise NotImplementedError()
        # _output.write_text(translated["kiara_models.fbs"])
    else:
        for model, text in translated.items():
            print("# ==========================================")
            print(f"# {model}")
            print(text)


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

    kiara_api: KiaraAPI = ctx.obj.kiara_api

    operation = kiara_api.get_operation(operation=operation_id)

    html = operation.create_html()
    print(html)


@dev_group.command("lineage-graph")
@click.argument("value", nargs=1)
@click.pass_context
def lineage_graph(ctx, value: str):
    """ "Print the lineage of a value as graph."""

    from kiara.utils.graphs import print_ascii_graph

    kiara_api: KiaraAPI = ctx.obj.kiara_api

    _value = kiara_api.get_value(value)
    graph = _value.lineage.full_graph

    print_ascii_graph(graph)
