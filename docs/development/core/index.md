# Development setup

This section outlines how to set up a development environment for *kiara*. For now, it is basically a description of how I setup my own environment, so you might or might not have to adapt some of those steps to your own needs, depending on the tools you use for Python development.

## Code checkout

The first step is to decide which source code repositories to check out. In most cases, you'll want to check out at least the following repositories:

- [kiara](https://github.com/DHARPA-Project/kiara)
- [kiara_plugin.core_types](https://github.com/DHARPA-Project/kiara_plugin.core_types)

In addition, it usually also makes sense to check out at least the `tabular` plugin, and probably the others as well, depending on what exactly you want to achive, and in which areas you want to work in:

- [kiara_plugin.tabular](https://github.com/DHARPA-Project/kiara_plugin.tabular)
- [kiara_plugin.onboarding](https://github.com/DHARPA-Project/kiara_plugin.onboarding)
- [kiara_plugin.network_analysis](https://github.com/DHARPA-Project/kiara_plugin.network_analysis)
- [kiara_plugin.language_processing](https://github.com/DHARPA-Project/kiara_plugin.language_processing)

Then there are the more frontend focussed projects:

- [kiara_plugin.html](https://github.com/DHARPA-Project/kiara_plugin.html)
- [kiara_plugin.service](https://github.com/DHARPA-Project/kiara_plugin.service)
- [kiara_plugin.streamlit](https://github.com/DHARPA-Project/kiara_plugin.streamlit)


### Script

I've written [a script](https://github.com/DHARPA-Project/kiara_plugin.develop/blob/main/scripts/development/install_dev_env.sh) to partly automate the process:

<div style='max-height:300px;overflow:auto'>
```bash
--8<--
../scripts/development/install_dev_env.sh
--8<--
```
</div>

Feel free to adapt it to your needs (for example, fork the repos you are in on Github, and change the `GITHUB_USER` variable to your own), and run it locally (on Linux or MacOS). You can start of with disabling most project repositories, and uncomment/add them later on, as needed, and re-run.

Before you run this script, make sure you have a virtualenv (or conda env) activated, otherwise the packages would be installed into your gloabl Python environment.


## IDE setup

This depends on your IDE, obviously. I use PyCharm, so what I do usually is:

- create a conda environment, activate it
- create the project base directory, `cd` into it
- run the checkout script above
- open PyCharm, and create a new project:
  - select your newly created base folder as project root directory
  - select my conda/virtualenv as 'existing' Python environment
- now, go through all sub-projects, individually, and mark the `src` folder as 'Sources Root' (right-click on the folder, select 'Mark Directory as' -> 'Sources Root'), and `tests` as 'Tests Sources Root"

I chose this setup instead of a monorepo because it makes it easier to release plugin packages independently of core *kiara*, as well as other plugin packages they might depend on. It makes setting up a development environment a bit harder (which is usually a one-time thing),
and it requires to do git commits/pushes/pulls independently for each sub-project, but so far the trade-off has been worth it.

Personally, I use [mu-repo](https://fabioz.github.io/mu-repo/) to manage multiple repositories like this, and it helps a bit cutting down in management tasks, I know there are other tools out there like this.
