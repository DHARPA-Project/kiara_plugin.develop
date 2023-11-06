# -*- coding: utf-8 -*-

#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)


import os
import sys
from pathlib import Path
from typing import Any, Union

import rich_click as click

from kiara.utils.cli import terminal_print

# if typing.TYPE_CHECKING:
#     from kiara_plugin.develop.conda import CondaEnvMgmt


@click.group("conda")
@click.pass_context
def conda(ctx):
    """Conda environment related sub-commands."""


@conda.command()
@click.argument("pkg_spec", nargs=1, required=True)
@click.option(
    "--publish", "-p", is_flag=True, help="Whether to upload the built package."
)
@click.option(
    "--user",
    "-u",
    help="If publishing is enabled, use this anaconda user instead of the one directly associated with the token.",
    required=False,
)
@click.option(
    "--token",
    "-t",
    help="If publishing is enabled, use this token to authenticate.",
    required=False,
)
@click.pass_context
def build_package_from_spec(
    ctx,
    pkg_spec: str,
    publish: bool = False,
    token: Union[str, None] = None,
    user: Union[str, None] = None,
):
    """Create a conda environment."""

    if publish and not token:
        if not os.environ.get("ANACONDA_PUSH_TOKEN"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no token provided. Either use the '--token' cli option or populate the 'ANACONDA_PUSH_TOKEN' environment variable."
            )
            sys.exit(1)

    from kiara.utils.files import get_data_from_file
    from kiara_plugin.develop.conda import CondaEnvMgmt, PkgSpec

    conda_mgmt: CondaEnvMgmt = CondaEnvMgmt()

    recipe_data = get_data_from_file(pkg_spec)
    pkg = PkgSpec(**recipe_data)

    pkg_result = conda_mgmt.build_package(pkg)
    if publish:
        conda_mgmt.upload_package(pkg_result, token=token, user=user)


@conda.command()
@click.argument("pkg")
@click.option("--version", "-v", help="The version of the package.", required=False)
@click.option(
    "--format",
    "-f",
    help="The format of the metadata.",
    type=click.Choice(["spec", "conda", "mamba", "raw"]),
    default="spec",
)
@click.option(
    "--output", "-o", help="Write to the specified file instead of printing to stdout."
)
@click.option("--force", help="Overwrite existing file.", is_flag=True)
@click.option(
    "--force-version", help="Overwrite the Python package version number.", is_flag=True
)
@click.option(
    "--patch-data", "-p", help="A file to patch the auto-generated spec with."
)
@click.pass_context
def build_package_spec(
    ctx,
    pkg: str,
    version: str,
    output,
    force: bool,
    format: str,
    force_version: bool,
    patch_data: Union[str, None] = None,
):
    """Create a conda package spec file."""

    import orjson
    from rich.syntax import Syntax

    from kiara.utils.json import orjson_dumps
    from kiara_plugin.develop.conda import CondaEnvMgmt

    if output:
        o = Path(output)
        if o.exists() and not force:
            terminal_print()
            terminal_print(f"Output path already exists: {output}. Doing nothing...")

    conda_mgmt: CondaEnvMgmt = CondaEnvMgmt()

    _patch_data = None
    if patch_data:
        from kiara.utils.files import get_data_from_file

        _patch_data = get_data_from_file(patch_data)

    pkg_metadata = conda_mgmt.get_pkg_metadata(
        pkg=pkg, version=version, force_version=force_version
    )

    spec = conda_mgmt.create_pkg_spec(pkg_metadata=pkg_metadata, patch_data=_patch_data)
    if format == "raw":
        pkg_out: str = orjson_dumps(pkg_metadata, option=orjson.OPT_INDENT_2)
        if not output:
            pkg_out = Syntax(pkg_out, "json")  # type: ignore
    elif format == "spec":
        pkg_out = spec.model_dump_json(indent=2)
        if not output:
            pkg_out = Syntax(pkg_out, "json")  # type: ignore
    elif format == "conda":
        pkg_out = spec.create_conda_spec()
    elif format == "mamba":
        pkg_out = spec.create_boa_recipe()
    else:
        terminal_print()
        terminal_print(f"Invalid format: {format}.")
        sys.exit(1)

    if not output:
        terminal_print(pkg_out)
    else:
        o = Path(output)
        o.mkdir(parents=True, exist_ok=True)
        if o.exists():
            os.unlink(o)
        o.write_text(pkg_out)


@conda.command()
@click.argument("pkg")
@click.option("--version", "-v", help="The version of the package.", required=False)
@click.option(
    "--patch-data", "-p", help="A file to patch the auto-generated spec with."
)
@click.option(
    "--publish", "-p", is_flag=True, help="Whether to upload the built package."
)
@click.option(
    "--user",
    "-u",
    help="If publishing is enabled, use this anaconda user instead of the one directly associated with the token.",
    required=False,
)
@click.option(
    "--token",
    "-t",
    help="If publishing is enabled, use this token to authenticate.",
    required=False,
)
@click.option(
    "--force-version", help="Overwrite the Python package version number.", is_flag=True
)
@click.pass_context
def build_package(
    ctx,
    pkg: str,
    version: str,
    publish: bool = False,
    user: Union[str, None] = None,
    token: Union[str, None] = None,
    patch_data: Union[str, None] = None,
    force_version: bool = False,
):
    """Create a conda environment."""

    from kiara_plugin.develop.conda import CondaEnvMgmt

    if publish and not token:
        if not os.environ.get("ANACONDA_PUSH_TOKEN"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no token provided. Either use the '--token' cli option or populate the 'ANACONDA_PUSH_TOKEN' environment variable."
            )
            sys.exit(1)

    conda_mgmt: CondaEnvMgmt = CondaEnvMgmt()

    _patch_data: Any = None
    if patch_data:
        from kiara.utils.files import get_data_from_file

        _patch_data = get_data_from_file(patch_data)

    metadata = conda_mgmt.get_pkg_metadata(
        pkg=pkg, version=version, force_version=force_version
    )
    _pkg = conda_mgmt.create_pkg_spec(pkg_metadata=metadata, patch_data=_patch_data)

    terminal_print()
    terminal_print("Generated conda package spec:")
    terminal_print()
    terminal_print(_pkg.create_conda_spec())
    terminal_print()
    terminal_print("Building package...")
    pkg_result = conda_mgmt.build_package(_pkg)
    if publish:
        conda_mgmt.upload_package(pkg_result, token=token, user=user)

    terminal_print(pkg_result)
