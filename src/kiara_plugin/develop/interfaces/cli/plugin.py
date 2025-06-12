# -*- coding: utf-8 -*-
import os

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)
import sys
from typing import TYPE_CHECKING, Union

import rich_click as click
from boltons.strutils import slugify

from kiara.utils.cli import output_format_option, terminal_print, terminal_print_model

if TYPE_CHECKING:
    from kiara.api import Kiara
    from kiara.interfaces.python_api.base_api import BaseAPI


@click.group("plugin")
@click.pass_context
def plugin_group(ctx):
    """Kiara context related sub-commands."""


@plugin_group.command(name="create")
@click.argument("name", nargs=1, required=True)
@click.option(
    "--path",
    "-p",
    help="The path of the plugin. If not provided, the current working directory will be used.",
    required=False,
)
@click.pass_context
def create_plugin(ctx, name: str, path: Union[None, str]):
    """Create a new plugin."""

    from copier import run_copy

    if not path:
        path = os.getcwd()

    if not os.path.exists(path):
        os.makedirs(path)

    if not os.path.isdir(path):
        raise Exception(f"Path '{path}' is not a directory.")

    slug = slugify(name)
    if not slug.startswith("kiara_plugin."):
        project_dir = f"kiara_plugin.{slug}"
    else:
        project_dir = slug

    full_path = os.path.join(path, project_dir)

    run_copy("gh:DHARPA-Project/kiara_plugin_template.git", full_path, data={"project_name": name, "project_slug": slug})

    terminal_print(f"Created new plugin '{name}' in: {full_path}")
