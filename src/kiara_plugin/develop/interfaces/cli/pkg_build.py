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


@click.group("build")
@click.pass_context
def pkg_build(ctx):
    """Package build related sub-commands."""

@pkg_build.group()
@click.pass_context
def conda(ctx):
    """Rattler-build environment related sub-commands."""


@conda.command("pkg-from-spec")
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
@click.option(
    "--channel",
    "-c",
    help="The conda channel to publish to.",
    required=False
)
@click.option("--output-folder", "-o", help="The output folder for the built package.", required=False)
@click.pass_context
def build_package_from_spec(
    ctx,
    pkg_spec: str,
    publish: bool = False,
    token: Union[str, None] = None,
    user: Union[str, None] = None,
    channel: Union[str, None] = None,
    output_folder: Union[str, None] = None,
):
    """Create a conda environment."""

    if publish and not token:
        if not os.environ.get("ANACONDA_PUSH_TOKEN"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no token provided. Either use the '--token' cli option or populate the 'ANACONDA_PUSH_TOKEN' environment variable."
            )
            sys.exit(1)

    if publish and not user:
        if not os.environ.get("ANACONDA_OWNER"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no user provided. Either use the '--user' cli option or populate the 'ANACONDA_OWNER' environment variable."
            )
            sys.exit(1)

    if publish and not channel:
        if not os.environ.get("ANACONDA_CHANNEL"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no channel provided. Use the '--channel' cli option to set."
            )
            sys.exit(1)

    from kiara.utils.files import get_data_from_file
    from kiara_plugin.develop.pkg_build.models import PkgSpec
    from kiara_plugin.develop.pkg_build.rattler import RattlerBuildEnvMgmt

    rattler_mgmt: RattlerBuildEnvMgmt = RattlerBuildEnvMgmt()

    recipe_data = get_data_from_file(pkg_spec)
    pkg = PkgSpec(**recipe_data)

    pkg_result = rattler_mgmt.build_package(pkg, output_folder=output_folder)
    if publish:
        rattler_mgmt.upload_package(artifacts_or_folder=pkg_result.build_artifacts, token=token, user=user, channel=channel)  # type: ignore


@conda.command("pkg-spec")
@click.argument("pkg")
@click.option("--version", "-v", help="The version of the package.", required=False)
@click.option(
    "--format",
    "-f",
    help="The format of the metadata.",
    type=click.Choice(["spec", "rattler-build", "raw"]),
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
    from kiara_plugin.develop.utils.pkg_utils import create_pkg_spec, get_pkg_metadata

    if output:
        o = Path(output)
        if o.exists() and not force:
            terminal_print()
            terminal_print(f"Output path already exists: {output}. Doing nothing...")

    _patch_data = None
    if patch_data:
        from kiara.utils.files import get_data_from_file

        _patch_data = get_data_from_file(patch_data)

    pkg_metadata = get_pkg_metadata(
        pkg=pkg, version=version, force_version=force_version
    )

    spec = create_pkg_spec(pkg_metadata=pkg_metadata, patch_data=_patch_data)

    if format == "raw":
        pkg_out: Union[str, Syntax] = orjson_dumps(pkg_metadata, option=orjson.OPT_INDENT_2)
        if not output:
            pkg_out = Syntax(pkg_out, "json", background_color="default")  # type: ignore
    elif format == "spec":
        pkg_out = spec.model_dump_json(indent=2)
        if not output:
            pkg_out = Syntax(pkg_out, "json", background_color="default")  # type: ignore
    elif format == "rattler-build":
        pkg_out = spec.create_rattler_build_recipe()
        if not output:
            pkg_out = Syntax(pkg_out, "yaml", background_color="default")  # type: ignore
    else:
        terminal_print()
        terminal_print(f"Invalid format: {format}.")
        sys.exit(1)

    if not output:
        terminal_print(pkg_out)
    else:
        o = Path(output)
        o.parent.mkdir(parents=True, exist_ok=True)
        if o.exists():
            os.unlink(o)
        o.write_text(pkg_out)  # type: ignore


@conda.command("pkg")
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
    "--channel",
    "-c",
    help="The conda channel to publish to.",
    required=False
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
@click.option("--output-folder", "-o", help="The output folder for the built package.", required=False)
@click.pass_context
def build_package(
    ctx,
    pkg: str,
    version: str,
    publish: bool = False,
    user: Union[str, None] = None,
    token: Union[str, None] = None,
    channel: Union[str, None] = None,
    patch_data: Union[str, None] = None,
    force_version: bool = False,
    output_folder: Union[str, None] = None,
):
    """Create a conda environment."""

    from kiara_plugin.develop.pkg_build.rattler import RattlerBuildEnvMgmt
    from kiara_plugin.develop.utils.pkg_utils import create_pkg_spec, get_pkg_metadata

    if publish and not token:
        if not os.environ.get("ANACONDA_PUSH_TOKEN"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no token provided. Either use the '--token' cli option or populate the 'ANACONDA_PUSH_TOKEN' environment variable."
            )
            sys.exit(1)

    if publish and not user:
        if not os.environ.get("ANACONDA_OWNER"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no user provided. Either use the '--user' cli option or populate the 'ANACONDA_OWNER' environment variable."
            )
            sys.exit(1)

    if publish and not channel:
        if not os.environ.get("ANACONDA_CHANNEL"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no channel provided. Either use the '--channel' cli option or populate the 'ANACONDA_CHANNEL' environment variable."
            )
            sys.exit(1)


    rattler_mgmt: RattlerBuildEnvMgmt = RattlerBuildEnvMgmt()

    _patch_data: Any = None
    if patch_data:
        from kiara.utils.files import get_data_from_file

        _patch_data = get_data_from_file(patch_data)

    metadata = get_pkg_metadata(
        pkg=pkg, version=version, force_version=force_version
    )
    _pkg = create_pkg_spec(pkg_metadata=metadata, patch_data=_patch_data)

    terminal_print()
    terminal_print("Generated conda package spec:")
    terminal_print()
    terminal_print(_pkg.create_conda_spec())
    terminal_print()
    terminal_print("Building package...")
    pkg_result = rattler_mgmt.build_package(_pkg, output_folder=output_folder)
    if publish:
        rattler_mgmt.upload_package(artifacts_or_folder=pkg_result.build_artifacts, token=token, user=user, channel=channel)  # type: ignore

    terminal_print(pkg_result)

@conda.command("publish")
@click.argument("artifact_or_folder", nargs=-1, required=True)
@click.option(
    "--user",
    "-u",
    help="If publishing is enabled, use this anaconda user instead of the one directly associated with the token.",
    required=False,
)
@click.option(
    "--channel",
    "-c",
    help="The conda channel to publish to.",
    required=False
)
@click.option(
    "--token",
    "-t",
    help="If publishing is enabled, use this token to authenticate.",
    required=False,
)
@click.pass_context
def publish_conda_pkgs(ctx, artifact_or_folder,
    user: Union[str, None] = None,
    token: Union[str, None] = None,
    channel: Union[str, None] = None,):
    """Publish one or several conda packages."""

    from kiara_plugin.develop.pkg_build.rattler import RattlerBuildEnvMgmt

    if not token:
        if not os.environ.get("ANACONDA_PUSH_TOKEN"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no token provided. Either use the '--token' cli option or populate the 'ANACONDA_PUSH_TOKEN' environment variable."
            )
            sys.exit(1)

    if not user:
        if not os.environ.get("ANACONDA_OWNER"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no user provided. Either use the '--user' cli option or populate the 'ANACONDA_OWNER' environment variable."
            )
            sys.exit(1)

    if not channel:
        if not os.environ.get("ANACONDA_CHANNEL"):
            terminal_print()
            terminal_print(
                "Package publishing enabled, but no channel provided. Use the '--channel' cli option to set."
            )
            sys.exit(1)

    artifacts = []
    for artifact in artifact_or_folder:

        path = Path(os.path.expanduser(artifact)).absolute()

        if not path.exists():
            terminal_print()
            terminal_print(f"Path does not exist: {path.as_posix()}")
            sys.exit(1)

        if path.is_file():
            artifacts.append(path)
        elif path.is_dir():
            for f in path.iterdir():
                if f.is_file() and (f.name.endswith(".tar.bz2") or f.name.endswith(".conda")):
                    artifacts.append(f)

    terminal_print()
    terminal_print("Publishing conda packages:")
    for artifact in artifacts:
        terminal_print(f"  - {artifact}")


    rattler_mgmt: RattlerBuildEnvMgmt = RattlerBuildEnvMgmt()
    rattler_mgmt.upload_package(artifacts_or_folder=artifacts, token=token, user=user, channel=channel)  # type: ignore
