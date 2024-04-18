# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Union

import httpx

from kiara.utils.cli import terminal_print
from kiara_plugin.develop.conda.models import (
    DEFAULT_HOST_DEPENDENCIES,
    PkgSpec,
)


def default_stdout_print(msg):
    terminal_print(f"[green]stdout[/green]: {msg}")


def default_stderr_print(msg):
    terminal_print(f"[red]stderr[/red]: {msg}")

# def extract_reqs_from_metadata(
#         pkg_metadata: Mapping[str, Any], extras: Union[None, Iterable[str]] = None
# ) -> Dict[str, Dict[str, Any]]:
#     reqs = pkg_metadata.get("requires_dist", None)
#
#     if not reqs:
#         return {}
#
#     filtered_reqs: Dict[str, Dict[str, Any]] = {}
#     extras_reqs = {}
#     for r in reqs:
#         tokens = r.split(";")
#         if len(tokens) == 1:
#             pkg_tokens = tokens[0].strip().split(" ")
#             if len(pkg_tokens) == 1:
#                 pkg = pkg_tokens[0]
#                 ver = None
#             elif len(pkg_tokens) == 2:
#                 pkg = pkg_tokens[0]
#                 if pkg_tokens[1][0] == "(":
#                     min = 1
#                 else:
#                     min = 0
#                 if pkg_tokens[1][-1] == ")":
#                     max = -1
#                 else:
#                     max = len(pkg_tokens[1])
#                 ver = pkg_tokens[1][min:max]
#             else:
#                 raise Exception(f"Can't parse version for pkg: {tokens[0]}")
#             cond = None
#         elif len(tokens) == 2:
#             if "extra" in tokens[1]:
#                 extra_start = tokens[1].index("extra == ")
#                 substr = tokens[1][extra_start + 10:]
#                 try:
#                     extra_stop = substr.index("'")
#                 except ValueError:
#                     extra_stop = substr.index('"')
#
#                 extra_name = substr[0:extra_stop]
#                 # TODO: multiple extras possible?
#                 if not extras or extra_name not in extras:
#                     continue
#             cond = tokens[1].strip()
#             pkg_tokens = tokens[0].strip().split(" ")
#             if len(pkg_tokens) == 1:
#                 pkg = pkg_tokens[0]
#                 ver = None
#             elif len(pkg_tokens) == 2:
#                 pkg = pkg_tokens[0]
#                 ver = pkg_tokens[1][1:-1]
#             else:
#                 raise Exception(f"Can't parse version for pkg: {tokens[0]}")
#             if ver:
#                 ver = ver[1:-1]
#
#         else:
#             raise Exception(f"Can't parse requirement: {r}")
#
#         if pkg in filtered_reqs.keys():
#             raise Exception(f"Duplicate req: {pkg}")
#
#         if "[" in pkg:
#             extras_pkg = pkg[0: pkg.index("[")]
#             extras_substr = pkg[pkg.index("[") + 1:]
#             extras_str = extras_substr[: extras_substr.index("]")]
#             extras_list = extras_str.split(",")
#             extras_reqs[extras_pkg] = extras_list
#             assert extras_pkg not in filtered_reqs.keys()
#             filtered_reqs[extras_pkg] = {"version": ver, "condition": cond}
#         else:
#             assert pkg not in filtered_reqs.keys()
#             filtered_reqs[pkg] = {"version": ver, "condition": cond}
#
#     for extra_pkg, extras in extras_reqs.items():
#         # version = filtered_reqs[extra_pkg]["version"]
#         # TODO: figure out the right version if there's a condition
#         version = None
#         req_metadata = get_pkg_metadata_from_pypi(
#             pkg_name=extra_pkg, version=version
#         )
#         new_reqs = extract_reqs_from_metadata(req_metadata, extras=extras)
#         for k, v in new_reqs.items():
#             if k in filtered_reqs.keys():
#                 continue
#             filtered_reqs[k] = v
#
#     fixed = {}
#     for k in sorted(filtered_reqs.keys()):
#         if k.startswith("kiara-plugin"):
#             fixed[k.replace("-", "_")] = filtered_reqs[k]
#         else:
#             fixed[k] = filtered_reqs[k]
#
#     return fixed


def get_pkg_metadata_from_pypi(
        pkg_name: str,
        version: Union[str, None, int, float] = None,
        extras: Union[None, Iterable[str]] = None,
    ) -> Mapping[str, Any]:

        result: Mapping[str, Any] = get_all_pkg_data_from_pypi(
            pkg_name=pkg_name, version=version, extras=extras
        )
        _result: MutableMapping[str, Any] = result["info"]
        _result["releases"] = result["releases"]
        return _result


def get_all_pkg_data_from_pypi(
        pkg_name: str,
        version: Union[str, None, int, float] = None,
        extras: Union[Iterable[str], None] = None,
    ) -> Mapping[str, Any]:

        if version:
            url = f"https://pypi.org/pypi/{pkg_name}/{version}/json"
        else:
            url = f"https://pypi.org/pypi/{pkg_name}/json"

        result = httpx.get(url)

        if result.status_code >= 300:
            raise Exception(
                f"Could not retrieve information for package '{pkg_name}': {result.text}"
            )

        pkg_metadata: Mapping[str, Any] = result.json()
        return pkg_metadata


def extract_reqs_from_metadata(
        pkg_metadata: Mapping[str, Any], extras: Union[None, Iterable[str]] = None
    ) -> Dict[str, Dict[str, Any]]:

        reqs = pkg_metadata.get("requires_dist", None)

        if not reqs:
            return {}

        filtered_reqs: Dict[str, Dict[str, Any]] = {}
        extras_reqs = {}
        for r in reqs:
            tokens = r.split(";")
            if len(tokens) == 1:
                pkg_tokens = tokens[0].strip().split(" ")
                if len(pkg_tokens) == 1:
                    pkg = pkg_tokens[0]
                    ver = None
                elif len(pkg_tokens) == 2:
                    pkg = pkg_tokens[0]
                    if pkg_tokens[1][0] == "(":
                        min = 1
                    else:
                        min = 0
                    if pkg_tokens[1][-1] == ")":
                        max = -1
                    else:
                        max = len(pkg_tokens[1])
                    ver = pkg_tokens[1][min:max]
                else:
                    raise Exception(f"Can't parse version for pkg: {tokens[0]}")
                cond = None
            elif len(tokens) == 2:
                if "extra" in tokens[1]:
                    extra_start = tokens[1].index("extra == ")
                    substr = tokens[1][extra_start + 10 :]
                    try:
                        extra_stop = substr.index("'")
                    except ValueError:
                        extra_stop = substr.index('"')

                    extra_name = substr[0:extra_stop]
                    # TODO: multiple extras possible?
                    if not extras or extra_name not in extras:
                        continue
                cond = tokens[1].strip()
                pkg_tokens = tokens[0].strip().split(" ")
                if len(pkg_tokens) == 1:
                    pkg = pkg_tokens[0]
                    ver = None
                elif len(pkg_tokens) == 2:
                    pkg = pkg_tokens[0]
                    ver = pkg_tokens[1][1:-1]
                else:
                    raise Exception(f"Can't parse version for pkg: {tokens[0]}")
                if ver:
                    ver = ver[1:-1]

            else:
                raise Exception(f"Can't parse requirement: {r}")

            if pkg in filtered_reqs.keys():
                raise Exception(f"Duplicate req: {pkg}")

            if "[" in pkg:
                extras_pkg = pkg[0 : pkg.index("[")]
                extras_substr = pkg[pkg.index("[") + 1 :]
                extras_str = extras_substr[: extras_substr.index("]")]
                extras_list = extras_str.split(",")
                extras_reqs[extras_pkg] = extras_list
                assert extras_pkg not in filtered_reqs.keys()
                filtered_reqs[extras_pkg] = {"version": ver, "condition": cond}
            else:
                assert pkg not in filtered_reqs.keys()
                filtered_reqs[pkg] = {"version": ver, "condition": cond}

        for extra_pkg, extras in extras_reqs.items():
            # version = filtered_reqs[extra_pkg]["version"]
            # TODO: figure out the right version if there's a condition
            version = None
            req_metadata = get_pkg_metadata_from_pypi(
                pkg_name=extra_pkg, version=version
            )
            new_reqs = extract_reqs_from_metadata(req_metadata, extras=extras)
            for k, v in new_reqs.items():
                if k in filtered_reqs.keys():
                    continue
                filtered_reqs[k] = v

        fixed = {}
        for k in sorted(filtered_reqs.keys()):
            if k.startswith("kiara-plugin"):
                fixed[k.replace("-", "_")] = filtered_reqs[k]
            else:
                fixed[k] = filtered_reqs[k]

        return fixed

def get_pkg_metadata(
    pkg: str,
    version: Union[str, None, int, float] = None,
    force_version: bool = False,
) -> Mapping[str, Any]:

    path = os.path.realpath(os.path.expanduser(pkg))
    if os.path.isdir(path):
        if version:
            if not force_version:
                raise Exception(
                    "Specified project is a local folder, using 'version' with this does not make sense. Use the 'force_version' argument if necessary."
                )

            _version: Union[None, str] = str(version)
        else:
            _version = None
        pkg_metadata = get_pkg_metadata_from_project_folder(
            path, force_version=_version
        )

    else:
        pkg_metadata = get_pkg_metadata_from_pypi(
            pkg_name=pkg, version=version
        )

    return pkg_metadata


def get_pkg_metadata_from_project_folder(
        project_path: str, force_version: Union[str, None] = None
    ) -> Mapping[str, Any]:

    from build.util import project_wheel_metadata

    wheel_data = project_wheel_metadata(project_path)

    requires_dist = []

    metadata = {}
    for k, v in wheel_data.items():  # type: ignore

        # if len(v) > 100:
        #     val = str(v)[0:100] + "..."
        # else:
        #     val = str(v)
        # print(f"- {k}: {val}")


        if k == "License":
            metadata["license"] = v
        elif k == "Project-URL" and "homepage" in v:
            metadata["home_page"] = v.split(",")[1].strip()
        elif k == "Summary":
            metadata["summary"] = v
        elif k == "Name":
            metadata["name"] = v
        elif k == "Version":
            metadata["version"] = v
        elif k == "Requires-Dist":
            requires_dist.append(v)


    metadata["releases"] = {}
    metadata["releases"][metadata["version"]] = [
        {"url": Path(project_path).absolute().as_posix(), "packagetype": "project_folder"}
    ]
    metadata["requires_dist"] = requires_dist

    return metadata

    # import sys
    # sys.exit()
    #
    #
    # build_env_details = self.get_state_details("conda-build-env")
    # env_name = build_env_details["env_name"]
    # prefix = build_env_details["mamba_prefix"]
    #
    # project_path = os.path.abspath(
    #     os.path.realpath(os.path.expanduser(project_path))
    # )
    # if project_path.endswith(os.path.sep):
    #     project_path = project_path[0:-1]
    #
    # pip_cmd = os.path.join(prefix, env_name, "bin", "pip")
    # args = ["install", "--quiet", "--dry-run", "--report", "-", project_path]
    #
    # run_result = execute(pip_cmd, *args)
    # pkg_metadata = json.loads(run_result.stdout)
    # install_list = pkg_metadata["install"]
    # result: Union[MutableMapping[str, Any], None] = None
    # for install_item in install_list:
    #     # TODO: windows?
    #     if (
    #         install_item.get("download_info", {}).get("url", "")
    #         == f"file://{project_path}"
    #     ):
    #         result = install_item["metadata"]
    # if not result:
    #     raise Exception(f"Could not parse package metadata for: {project_path}")
    #
    # folder_name = os.path.basename(project_path)
    # if folder_name != result["name"]:
    #     if folder_name == result["name"].replace("-", "_"):
    #         result["name"] = folder_name
    #     elif folder_name.startswith("kiara_plugin.") and result["name"].startswith(
    #         "kiara-plugin"
    #     ):
    #         result["name"] = result["name"].replace("-", "_", 1)
    #
    # assert "releases" not in result.keys()
    #
    # if force_version:
    #     result["version"] = force_version
    # version = result["version"]
    # result["releases"] = {}
    # result["releases"][version] = [
    #     {"url": f"file://{project_path}", "packagetype": "project_folder"}
    # ]
    # return result


def create_pkg_spec(
        pkg_metadata: Mapping[str, Any],
        patch_data: Union[None, Mapping[str, Any]] = None,
    ) -> PkgSpec:

        req_repl_dict: Union[None, Mapping[str, str]] = None
        if patch_data:
            req_repl_dict = patch_data.get("requirements", None)

        requirements = extract_reqs_from_metadata(pkg_metadata=pkg_metadata)

        req_list = []
        for k, v in requirements.items():
            if req_repl_dict and k in req_repl_dict.keys():
                repl = req_repl_dict[k]
                if repl:
                    req_list.append(req_repl_dict[k])
            else:
                if not v.get("version"):
                    pkg_str = k
                else:
                    pkg_str = f"{k} {v['version']}"
                req_list.append(pkg_str)

        pkg_name = pkg_metadata["name"]
        version = pkg_metadata["version"]

        # all_data = self.get_all_pkg_data_from_pypi(pkg_name=pkg_name)

        releases = pkg_metadata["releases"]
        if pkg_metadata["version"] not in releases.keys():
            raise Exception(
                f"Could not find release '{version}' data for package '{pkg_name}'."
            )

        version_data = releases[pkg_metadata["version"]]

        pkg_hash = None
        pkg_url = None
        pkg_is_local = False
        for v in version_data:
            if v["packagetype"] == "project_folder":
                pkg_hash = None
                pkg_url = v["url"]
                pkg_is_local = True
                break

        if pkg_hash is None:
            for v in version_data:
                if v["packagetype"] == "sdist":
                    pkg_hash = v["digests"]["sha256"]
                    pkg_url = v["url"]
                    break

        if pkg_hash is None:
            for v in version_data:
                if v["packagetype"] == "bdist_wheel":
                    # TODO: make sure it's a universal wheel
                    pkg_hash = v["digests"]["sha256"]
                    pkg_url = v["url"]

        if pkg_url is None:
            raise Exception(f"Could not find hash for package: {pkg_name}.")

        pkg_requirements = req_list
        if patch_data and "channels" in patch_data.keys():
            pkg_channels = patch_data["channels"]
        else:
            pkg_channels = ["conda-forge"]
        recipe_maintainers = ["frkl"]

        if patch_data and "host_requirements" in patch_data.keys():
            host_requirements = patch_data["host_requirements"]
        else:
            host_requirements = DEFAULT_HOST_DEPENDENCIES()

        if patch_data and "test" in patch_data.keys():
            test_spec = patch_data["test"]
        else:
            test_spec = {}

        home_page = pkg_metadata.get("home_page", None)
        if not home_page:
            for url_type, url in pkg_metadata.get("project_urls", {}).items():
                if url_type == "homepage":
                    home_page = url
                    break

        if (
            patch_data
            and "entry_points" in patch_data.keys()
            and patch_data["entry_points"]
        ):
            entry_points = patch_data["entry_points"]
        else:
            entry_points = {}

        license = pkg_metadata.get("license")
        enforce_spdx = True

        if enforce_spdx:
            from license_expression import get_spdx_licensing
            licensing = get_spdx_licensing()
            if license not in licensing.known_symbols.keys():
                license = f"LicenseRef-{license}"

        spec_data = {
            "pkg_name": pkg_name,
            "pkg_version": pkg_metadata["version"],
            "pkg_hash": pkg_hash,
            "pkg_url": pkg_url,
            "pkg_is_local": pkg_is_local,
            "host_requirements": host_requirements,
            "pkg_requirements": pkg_requirements,
            "pkg_channels": pkg_channels,
            "metadata": {
                "home": home_page,
                "license": license,
                "summary": pkg_metadata.get("summary"),
                "recipe_maintainers": recipe_maintainers,
            },
            "test": test_spec,
            "entry_points": entry_points,
        }
        return PkgSpec(**spec_data)
