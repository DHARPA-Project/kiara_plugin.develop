# -*- coding: utf-8 -*-
# helper function, from: https://gist.github.com/thelinuxkid/5114777
import selectors
import subprocess
from pathlib import Path
from subprocess import Popen
from typing import Callable, Generator, Union

from kiara_plugin.develop.conda import RunDetails

newlines = ["\n", "\r\n", "\r"]


def unbuffered(
    proc: Popen, stdout_prefix: str = "", stderr_prefix: str = ""
) -> Generator[str, None, None]:

    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)  # type: ignore
    sel.register(proc.stderr, selectors.EVENT_READ)  # type: ignore
    current_stdout = ""
    current_stderr = ""

    stdout_finished = False
    stderr_finished = False

    while True:
        for key, _ in sel.select():
            data = key.fileobj.read(1)  # type: ignore
            if not data:
                if key.fileobj == proc.stdout:
                    stdout_finished = True
                else:
                    stderr_finished = True

                if stdout_finished and stderr_finished:
                    break

            if key.fileobj is proc.stdout:
                if data in newlines:
                    yield stdout_prefix + current_stdout
                    current_stdout = ""
                else:
                    current_stdout += data
            elif data in newlines:
                yield stderr_prefix + current_stderr
                current_stderr = ""
            else:
                current_stderr += data
        else:
            continue

        break


class ExecutionException(Exception):
    def __init__(self, msg, run_details: RunDetails):
        self._run_details = run_details
        super().__init__(msg)

    @property
    def run_details(self) -> RunDetails:
        return self._run_details


def execute(
    cmd: str,
    *args: str,
    stdout_callback: Union[Callable, None] = None,
    stderr_callback: Union[Callable, None] = None,
    cwd: Union[None, str, Path] = None,
) -> RunDetails:

    stdout_output = []
    stderr_output = []
    _args = list(args)
    with subprocess.Popen(
        [cmd,*_args],
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=cwd,
    ) as proc:
        for line in unbuffered(proc, stdout_prefix="o-", stderr_prefix="e-"):
            if line.startswith("o-"):
                _line = line[2:]
                if stdout_callback:
                    stdout_callback(_line)
                stdout_output.append(_line)
            elif line.startswith("e-"):
                _line = line[2:]
                if stderr_callback:
                    stderr_callback(_line)
                stderr_output.append(_line)

        proc.wait()
        run_details = RunDetails(
            cmd=cmd,
            args=_args,
            exit_code=proc.returncode,
            stdout="\n".join(stdout_output),
            stderr="\n".join(stderr_output),
        )

    if run_details.exit_code != 0:
        raise ExecutionException(
            f"Failed to run command '{cmd} {' '.join(args)}'", run_details=run_details
        )
    return run_details
