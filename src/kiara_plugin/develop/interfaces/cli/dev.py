# -*- coding: utf-8 -*-

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)
import os
import os.path
import shutil
import sys
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, List, Tuple

import rich_click as click
from kiara import KiaraAPI
from kiara.context import Kiara
from kiara.interfaces.python_api.models.info import (
    KiaraModelClassesInfo,
    KiaraModelTypeInfo,
)
from kiara.utils.cli import output_format_option, terminal_print, terminal_print_model
from kiara.utils.graphs import print_ascii_graph
from pydantic2ts.cli.script import generate_json_schema, remove_master_model_from_output


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

    kiara: Kiara = ctx.obj["kiara"]

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

    kiara: Kiara = ctx.obj["kiara"]
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

    kiara_api: KiaraAPI = ctx.obj["kiara_api"]

    operation = kiara_api.get_operation(operation_id=operation_id)
    tree = operation.create_renderable_tree(show_data=show_data)
    terminal_print(tree)


@model.group(name="html")
@click.pass_context
def html(ctx):
    """Utilities to do html-related tasks with kiara models."""


@html.command()
@click.argument("filter", nargs=-1)
@click.option(
    "--check-module-name",
    "-m",
    help="If using filters, compare the filters against the full Python path (incl. module path), not just the class name.",
    is_flag=True,
)
@click.option("--output", "-o", help="The file to write the output", required=True)
@click.option("--delete", "-d", help="Delete file if exists.", is_flag=True)
@click.option("--append", "-a", help="Append to file if exists.", is_flag=True)
@click.pass_context
def create_typescript_models(
    ctx,
    filter: Tuple[str],
    check_module_name: bool,
    output: str,
    delete: bool,
    append: bool,
):
    """Create typescript models"""

    def generate_typescript_defs(
        models: List[Any],
        output: str,
        exclude: Tuple[str, ...] = (),
        json2ts_cmd: str = "json2ts",
    ) -> None:
        """
        Convert the pydantic models in a python module into typescript interfaces.

        :param models: the models
        :param output: file that the typescript definitions will be written to
        :param exclude: optional, a tuple of names for pydantic models which should be omitted from the typescript output.
        :param json2ts_cmd: optional, the command that will execute json2ts. Use this if it's installed in a strange spot.
        """
        if not shutil.which(json2ts_cmd):
            raise Exception(
                "json2ts must be installed. Instructions can be found here: "
                "https://www.npmjs.com/package/json-schema-to-typescript"
            )

        if exclude:
            models = [m for m in models if m.__name__ not in exclude]

        schema = generate_json_schema(models)
        schema_dir = mkdtemp()
        schema_file_path = os.path.join(schema_dir, "schema.json")

        with open(schema_file_path, "w") as f:
            f.write(schema)

        os.system(f'{json2ts_cmd} -i {schema_file_path} -o {output} --bannerComment ""')
        shutil.rmtree(schema_dir)
        remove_master_model_from_output(output)

    output_file = Path(output)
    if output_file.exists() and not delete and not append:
        terminal_print()
        terminal_print(
            f"File '{output}' exists, and neither 'force' nor 'append' specified. Doing nothing..."
        )
        sys.exit(1)

    kiara: Kiara = ctx.obj["kiara"]

    final_filters: List[str] = []
    for f in filter:
        if os.path.isfile(os.path.realpath(f)):
            lines = Path(f).read_text().splitlines()
            final_filters.extend((line.strip() for line in lines))
        else:
            final_filters.append(f.strip())

    all_models = kiara.kiara_model_registry.all_models
    if filter:
        _temp = {}
        for model_id, model_cls in all_models.item_infos.items():
            match = False
            for f in final_filters:
                if check_module_name:
                    token = model_cls.python_class.full_name
                else:
                    token = model_cls.python_class.python_class_name
                if f.lower() in token.lower() or f.lower() in token.lower():
                    match = True
                    break
            if match:
                _temp[model_id] = model_cls
        all_models = KiaraModelClassesInfo(
            group_title="Filtered models", item_infos=_temp
        )

    if not all_models:
        terminal_print()
        terminal_print("No matching models found. Doing nothing...")
        sys.exit(1)

    model_infos: List[KiaraModelTypeInfo] = list(all_models.item_infos.values())

    terminal_print()
    terminal_print("Exporting models:")
    terminal_print_model(all_models)
    terminal_print()
    models = [m.python_class.get_class() for m in model_infos]

    # temp = tempfile.NamedTemporaryFile(suffix='_temp', prefix='kiara_model_gen_')
    if output_file.exists() and delete:
        os.unlink(output_file)
    generate_typescript_defs(models, output=output_file.as_posix())

    # all_content = []
    # all_model_paths = set()
    # for model in models:
    #     model_path = model.python_class.get_python_module().__file__
    #     all_model_paths.add(model_path)
    #
    # for model_path in all_model_paths:
    #     temp = tempfile.NamedTemporaryFile(suffix='_temp', prefix='kiara_model_gen_')
    #     generate_typescript_defs(module=model_path, output=temp.name)
    #     all_content.append(Path(temp.name).read_text())
    #     temp.close()
    # with output_file.open(mode='ta') as f:
    #     for c in all_content:
    #         f.write(c + "\n\n")


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

    kiara_api: KiaraAPI = ctx.obj["kiara_api"]

    operation = kiara_api.get_operation(operation_id=operation_id)

    html = operation.create_html()
    print(html)


@dev_group.command("lineage-graph")
@click.argument("value", nargs=1)
@click.pass_context
def lineage_graph(ctx, value: str):
    """ "Print the lineage of a value as graph."""

    kiara_api: KiaraAPI = ctx.obj["kiara_api"]

    _value = kiara_api.get_value(value)
    graph = _value.lineage.full_graph

    print_ascii_graph(graph)
