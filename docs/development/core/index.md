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

I've written a script to partly automate the process:

--8<--
scripts/development/install_dev_env.sh
--8<--
