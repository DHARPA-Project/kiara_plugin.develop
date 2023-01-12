# Usage

This page outlines the utilities included in this package, this is not necessarily required for *kiara* development.

## Installation

To install this package, run (within an activated virtual environment):

```bash
```bash
pip install kiara_plugin.develop
# or, when using conda
conda install kiara_plugin.develop
```

After installation, `kiara --help` should include the `dev` subcommand:

{{ cli("kiara", "--help", max_height=240, split_command_and_output=False, extra_env={"KIARA_CONTEXT": "_doc", "CONSOLE_WIDTH": "200"}) }}

## Create new project

- create project in Github
- git remote add origin git@github.com:<PROJECT_USER>/<PROJECT_NAME>
- git push -u origin develop
