
Setup your own Compatibility Patcher
=================================================

To make a new framework/library (here called the **software**) benefit from such a companion application, we recommend
starting from the provided project skeleton.

It provides a standard structure for utilities and sets of fixers (preventing import loops), and activates several
helpers: checking that every fixer has its test, checking that no stdlib "warnings.warn()" is directly used by
compatibility shims, checking that Tox properly tests the setuptools-deployed package and not the one of the "src/"
directory, generating a readme file with the list of available fixers...

It also provides basic metadata files for packaging, as well as Pytest/Tox integration, Travis integration for
Continuous Integration of your Git repository..


Prerequisites
---------------------------------

As usual, it is advised that you create and activate a separate python virtual environment before working an a new
project.

Recent python versions will just need :code:`python -m venv <env_name>`, while older ones will use
:code:`virtualenv <env_name>` after installing `virtualenv` package, or :code:`mkvirtualenv <env_name>` if they prefer the
commodities of `virtualenvwrapper`.

Be sure that `your virtualenv is activated <https://virtualenv.pypa.io/en/stable/userguide/>`_ before proceeding
(:code:`pip freeze` should show an empty list of installed packages).

Then `install cookiecutter <https://cookiecutter.readthedocs.io/en/latest/installation.html>`_ as explained in their docs.


Deploying the project skeleton
-------------------------------------

The recipe for compatibility patchers is stored in the compat-patcher-core repository, so just do::

    cookiecutter https://github.com/pakal/compat-patcher-core

Enter the requested information, in particuler the **project_prefix** which should be the short name of the software
which you intend to provides comaptibility fixers for. By convention, your compatibility patcher should have a name
in the form "<software>-compat-patcher".

Then `cd` into the newly created project, and explore the few files that were templated for you.


Launching tests
------------------

You can run :code:`python setup.py test`, which will install test requirements in a temporary folder, and launch pytest.

But it is advised to install all dev dependencies in your virtualenv, and directly run :code:`pytest`::

    pip install -r requirements-dev.txt

    pytest

In case of failed tests, you might want to tweak the `pytest.ini` file, or directly ask for more verbosity::

    pytest -vl --tb=long -x

To test cross-version compatibility of your changes, run the :code:`tox` tool from inside the repository;
and ensure that eventually all combinations of Python and your to-be-patched framework are present in your `tox.ini` file.


Implementing software-specific patchers
----------------------------------------

Now begins the real value-added work:

- Adding your target software as a dependency, in `setup.py` and `requirements.txt`
- Fixing the implementation of `get_current_software_version()` (in `registry.py`) to fetch the real current version of said software
- Writing your first compatibility fixers, as well as their tests (look at the dummy `fix_behaviour_submodule_element()`
  and then remove it).
- Tweaking `README.in`, `CHANGELOG` and `CONTRIBUTING` according to your needs, and (re)generating the real `README.rst` with `generate_readme.py`
- Optionally modifying the root `patch()` function to fetch its default settings from the configuration files of your target framework

Note that if you don't plan to provide a standalone patcher, but an additional fixers registry for an existing Compatibility Patcher, you can remove all of the `patch()` functionality.





