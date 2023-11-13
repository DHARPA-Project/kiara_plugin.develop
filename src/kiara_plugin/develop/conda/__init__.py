# -*- coding: utf-8 -*-
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Union

import httpx
from diskcache import Cache

from kiara.utils.cli import terminal_print
from kiara_plugin.develop.conda.models import (
    DEFAULT_HOST_DEPENDENCIES,
    CondaBuildPackageDetails,
    PkgSpec,
    RunDetails,
)
from kiara_plugin.develop.conda.states import (
    MambaEnvironment,
    MicroMambaAvailable,
    States,
)
from kiara_plugin.develop.defaults import (
    DEFAULT_PYTHON_VERSION,
    KIARA_DEV_CACHE_FOLDER,
    KIARA_DEV_MICROMAMBA_ENV,
    KIARA_DEV_MICROMAMBA_TARGET_PREFIX,
)
from kiara_plugin.develop.utils import execute

CACHE_DIR = os.path.join(KIARA_DEV_CACHE_FOLDER, "pypi_cache")
cache = Cache(CACHE_DIR)


def default_stdout_print(msg):
    terminal_print(f"[green]stdout[/green]: {msg}")


def default_stderr_print(msg):
    terminal_print(f"[red]stderr[/red]: {msg}")


class CondaEnvMgmt(object):
    def __init__(self) -> None:

        self._states: States = States()
        self._states.add_state(
            MicroMambaAvailable(
                "micromamba_available", root_path=KIARA_DEV_CACHE_FOLDER, version="1.4.6"
            )
        )
        channels = ["conda-forge", "dharpa", "anaconda"]
        # deps = [f"python=={DEFAULT_PYTHON_VERSION}", "boa", "mamba", "anaconda"]
        deps = ["python==3.9", "boa", "mamba", "anaconda-client", "conda-verify"]
        conda_build_env = MambaEnvironment(
            "conda-build-env",
            env_name="conda-build-env",
            channels=channels,
            dependencies=deps,
            mamba_prefix=KIARA_DEV_MICROMAMBA_TARGET_PREFIX,
        )
        self._states.add_state(conda_build_env)
        channels = ["conda-forge", "dharpa"]
        deps = [f"python=={DEFAULT_PYTHON_VERSION}", "pip"]
        test_env = MambaEnvironment(
            "test-env",
            env_name="test-env",
            channels=channels,
            dependencies=deps,
            mamba_prefix=KIARA_DEV_MICROMAMBA_TARGET_PREFIX,
        )
        self._states.add_state(test_env)

    def get_state_detail(self, state_id: str, key: str) -> Any:

        return self._states.get_state_detail(state_id, key)

    def get_state_details(self, state_id: str):
        return self._states.get_state_details(state_id)

    def get_state(self, state_id: str):
        return self._states.get_state(state_id)

    def list_conda_envs(self) -> List[str]:

        micromamba_path = self.get_state_detail(
            "micromamba_available", "micromamba_bin"
        )

        args = [micromamba_path, "env", "list", "--json"]
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
            shell=False,
            env=KIARA_DEV_MICROMAMBA_ENV,
        )

        envs = json.loads(result.stdout)
        return [
            x[len(KIARA_DEV_MICROMAMBA_TARGET_PREFIX) + 1 :]
            for x in envs["envs"]
            if x.startswith(KIARA_DEV_MICROMAMBA_TARGET_PREFIX)
        ]

    def build_package(
        self, package: PkgSpec, python_version=DEFAULT_PYTHON_VERSION
    ) -> CondaBuildPackageDetails:

        build_env_details = self.get_state_details("conda-build-env")
        env_name = build_env_details["env_name"]
        prefix = build_env_details["mamba_prefix"]
        conda_bin = os.path.join(prefix, env_name, "bin", "conda")

        # tempdir = tempfile.TemporaryDirectory()
        # base_dir = tempdir.name
        base_dir = os.path.join(
            KIARA_DEV_CACHE_FOLDER,
            "build",
            package.pkg_name,
            package.pkg_version,
            f"python-{python_version}",
        )

        build_dir = Path(base_dir) / "build"
        if build_dir.is_dir():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=False)

        meta_file = Path(base_dir) / "meta.yaml"
        recipe = package.create_conda_spec()
        with open(meta_file, "wt") as f:
            f.write(recipe)

        channels = [
            item
            for tokens in (("--channel", channel) for channel in package.pkg_channels)
            for item in tokens
        ]

        args = ["mambabuild", "--py", python_version]
        args.extend(channels)
        args.extend(["--output-folder", build_dir.as_posix(), base_dir])

        result = execute(
            conda_bin,
            *args,
            stdout_callback=default_stdout_print,
            stderr_callback=default_stderr_print,
        )

        artifact = os.path.join(
            build_dir,
            "noarch",
            f"{package.pkg_name}-{package.pkg_version}-py_0.tar.bz2",
        )
        if not Path(artifact).is_file():
            raise Exception(f"Invalid artifact path: {artifact}")

        result = CondaBuildPackageDetails(
            cmd=conda_bin,
            args=args[1:],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            base_dir=base_dir,
            build_dir=build_dir.as_posix(),
            meta_file=meta_file.as_posix(),
            package=package,
            build_artifact=artifact,
        )
        return result

    def upload_package(
        self,
        build_result: Union[CondaBuildPackageDetails, str, Path],
        token: Union[str, None] = None,
        user: Union[None, str] = None,
    ):

        if isinstance(build_result, str):
            artifact = build_result
        elif isinstance(build_result, Path):
            artifact = build_result.as_posix()
        else:
            artifact = build_result.build_artifact

        build_env_details = self.get_state_details("conda-build-env")
        env_name = build_env_details["env_name"]
        prefix = build_env_details["mamba_prefix"]
        anaconda_bin = os.path.join(prefix, env_name, "bin", "anaconda")

        if token is None:
            token = os.getenv("ANACONDA_PUSH_TOKEN")
            if not token:
                raise Exception("Can't upload package, no api token provided.")

        args = ["-t", token, "upload"]
        if user:
            args.extend(["-u", user])

        args.append(os.path.expanduser(artifact))

        details = execute(
            anaconda_bin,
            *args,
            stdout_callback=default_stdout_print,
            stderr_callback=default_stderr_print,
        )

        terminal_print("Uploaded package, details:")
        terminal_print(details)



    def create_pkg_spec(
        self,
        pkg_metadata: Mapping[str, Any],
        patch_data: Union[None, Mapping[str, Any]] = None,
    ) -> PkgSpec:

        req_repl_dict: Union[None, Mapping[str, str]] = None
        if patch_data:
            req_repl_dict = patch_data.get("requirements", None)

        requirements = self.extract_reqs_from_metadata(pkg_metadata=pkg_metadata)

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
        for v in version_data:
            if v["packagetype"] == "project_folder":
                pkg_hash = None
                pkg_url = v["url"]
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
            for url in pkg_metadata.get("project_url", []):
                if url.startswith("homepage, "):
                    home_page = url[10:]
                    break

        if (
            patch_data
            and "entry_points" in patch_data.keys()
            and patch_data["entry_points"]
        ):
            entry_points = patch_data["entry_points"]
        else:
            entry_points = {}

        spec_data = {
            "pkg_name": pkg_name,
            "pkg_version": pkg_metadata["version"],
            "pkg_hash": pkg_hash,
            "pkg_url": pkg_url,
            "host_requirements": host_requirements,
            "pkg_requirements": pkg_requirements,
            "pkg_channels": pkg_channels,
            "metadata": {
                "home": home_page,
                "license": pkg_metadata.get("license"),
                "summary": pkg_metadata.get("summary"),
                "recipe_maintainers": recipe_maintainers,
            },
            "test": test_spec,
            "entry_points": entry_points,
        }

        return PkgSpec(**spec_data)

    def install_package_with_pip(
        self,
        env_dir: str,
        pkg_name: str,
        version: Union[str, None, int, float] = None,
        extras: Union[None, Iterable[str]] = None,
    ) -> RunDetails:

        pip_cmd = os.path.join(env_dir, "bin", "pip")
        full_name = pkg_name
        if version is not None:
            full_name = f"{full_name}=={version}"

        if extras:
            extras_str = ",".join(extras)
            full_name = f"{full_name}[{extras_str}]"

        args = ["install", full_name]
        result = execute(pip_cmd, *args, stdout_callback=None, stderr_callback=None)

        return result

    def install_local_package(
        self, env_dir, path: str, extras: Union[None, Iterable[str]] = None
    ):

        real_path = os.path.realpath(os.path.expanduser(path))
        if not os.path.isdir(real_path):
            raise Exception(
                f"Can't install python packge from path, path does not exist or is not a directory: {path}."
            )

        pip_cmd = os.path.join(env_dir, "bin", "pip")

        full_name = real_path
        if extras:
            extras_str = ",".join(extras)
            full_name = f"{full_name}[{extras_str}]"

        args = ["install", full_name]
        result = execute(pip_cmd, *args, stdout_callback=None, stderr_callback=None)

        return result

    # @cache.memoize(typed=True, tag='pypy_data')
    def get_all_pkg_data_from_pypi(
        self,
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

    def get_pkg_metadata(
        self,
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
            pkg_metadata = self.get_pkg_metadata_from_project_folder(
                path, force_version=_version
            )

        else:
            pkg_metadata = self.get_pkg_metadata_from_pypi(
                pkg_name=pkg, version=version
            )

        return pkg_metadata

    def get_pkg_metadata_from_pypi(
        self,
        pkg_name: str,
        version: Union[str, None, int, float] = None,
        extras: Union[None, Iterable[str]] = None,
    ) -> Mapping[str, Any]:

        result: Mapping[str, Any] = self.get_all_pkg_data_from_pypi(
            pkg_name=pkg_name, version=version, extras=extras
        )
        _result: MutableMapping[str, Any] = result["info"]
        _result["releases"] = result["releases"]
        return _result

    def get_pkg_metadata_from_project_folder(
        self, project_path: str, force_version: Union[str, None] = None
    ) -> Mapping[str, Any]:

        build_env_details = self.get_state_details("conda-build-env")
        env_name = build_env_details["env_name"]
        prefix = build_env_details["mamba_prefix"]

        project_path = os.path.abspath(
            os.path.realpath(os.path.expanduser(project_path))
        )
        if project_path.endswith(os.path.sep):
            project_path = project_path[0:-1]

        pip_cmd = os.path.join(prefix, env_name, "bin", "pip")
        args = ["install", "--quiet", "--dry-run", "--report", "-", project_path]

        run_result = execute(pip_cmd, *args)
        pkg_metadata = json.loads(run_result.stdout)
        install_list = pkg_metadata["install"]
        result: Union[MutableMapping[str, Any], None] = None
        for install_item in install_list:
            # TODO: windows?
            if (
                install_item.get("download_info", {}).get("url", "")
                == f"file://{project_path}"
            ):
                result = install_item["metadata"]
        if not result:
            raise Exception(f"Could not parse package metadata for: {project_path}")

        folder_name = os.path.basename(project_path)
        if folder_name != result["name"]:
            if folder_name == result["name"].replace("-", "_"):
                result["name"] = folder_name
            elif folder_name.startswith("kiara_plugin.") and result["name"].startswith(
                "kiara-plugin"
            ):
                result["name"] = result["name"].replace("-", "_", 1)

        assert "releases" not in result.keys()

        if force_version:
            result["version"] = force_version
        version = result["version"]
        result["releases"] = {}
        result["releases"][version] = [
            {"url": f"file://{project_path}", "packagetype": "project_folder"}
        ]
        return result

    def get_pkg_metadata_from_env(
        self, env_dir: str, pkg_name: str
    ) -> Mapping[str, Any]:

        python_cmd = os.path.join(env_dir, "bin", "python")

        args = [
            "-c",
            f"from importlib.metadata import metadata; import json; print(json.dumps(metadata('{pkg_name}').json));",
        ]
        result = execute(python_cmd, *args)

        pkg_metadata: Mapping[str, Any] = json.loads(result.stdout)
        # TODO: add 'releases' info
        return pkg_metadata

    def extract_reqs_from_metadata(
        self, pkg_metadata: Mapping[str, Any], extras: Union[None, Iterable[str]] = None
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
                    extra_stop = substr.index("'")
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
            req_metadata = self.get_pkg_metadata_from_pypi(
                pkg_name=extra_pkg, version=version
            )
            new_reqs = self.extract_reqs_from_metadata(req_metadata, extras=extras)
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
