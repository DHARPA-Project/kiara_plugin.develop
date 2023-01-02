# Kiara plugin packaging

Most of this is automated by the plugin template, there are  few things that need to be done before though.

We need 2 secret tokens, for pushing release artifacts to [pypi](https://pypi.org) and [anaconda](https://anaconda.org).

### `ANACONDA_PUSH_TOKEN`

Log into your [anaconda.org](https://anaconda.org) account, switch to the organization that hosts your package (if applicable), go to "Settings". Here, click 'Access' and create a token that has the:

- 'Allow read access to the API site'
- 'Allow write access to the API site'
- 'Allow all operations on Conda repositories'

items checked.

Copy both tokens and store it in your password manager (or enter it directly into a github secret).

### `PYPI_API_TOKEN`

On the Github account or organization you are using for your plugin, you need to have 2 secrets set:

- go to your github account/org "Settings" page
- on the navigation, click on "Secrets", then "Actions"
- click 'Create new [organization/account] secret'
- add the token strings for the environment variable names you created
