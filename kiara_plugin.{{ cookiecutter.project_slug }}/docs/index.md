# [**kiara**](https://dharpa.org/kiara.documentation) plugin: {{ cookiecutter.project_name }}

This package contains a set of commonly used/useful modules, pipelines, types and metadata schemas for [*Kiara*](https://github.com/DHARPA-project/kiara).

## Description

{{ cookiecutter.project_short_description }}

## Package content

{% raw %}{% for item_type, item_group in get_context_info().get_all_info().items() %}

### {{ item_type }}
{% for item, details in item_group.item_infos.items() %}
- [`{{ item }}`][kiara_info.{{ item_type }}.{{ item }}]: {{ details.documentation.description }}
{% endfor %}
{% endfor %}{% endraw %}

## Links

 - Documentation: [https://{{ cookiecutter.github_user }}.github.io/kiara_plugin.{{ cookiecutter.project_slug }}](https://{{ cookiecutter.github_user }}.github.io/kiara_plugin.{{ cookiecutter.project_slug }})
 - Code: [https://github.com/{{ cookiecutter.github_user }}/kiara_plugin.{{ cookiecutter.project_slug }}](https://github.com/{{ cookiecutter.github_user }}/kiara_plugin.{{ cookiecutter.project_slug }})
