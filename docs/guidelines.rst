Guidelines
#######################

In the following documentation, the **software** represents the application/framework/library for which the compat-patcher
companion application is implemented.

To make a new framework/library benefit from such a compat-patcher, we recommend starting from the
provided project skeleton :

COMING SOON

.. TODO ADD COOKIE-CUTTER RECIPE

This skeleton provides a standard structure for utilities and sets of fixers, and activates several helpers: checking that every fixer has its test (when using pytest), checking that no stdlib "warnings.warn()" is used by compatibility shims, autogenerating a Readme with the list of available fixers...

.. Then, provide the `current_software_version` to the registry constructor, possibly as a callable.

.. TODO PUT THESE INIT STEPS IN RECIPE INSTEAD!!!


Writing new fixers
--------------------

- Follow PEP8 as much as you can, or use `Black <https://pypi.org/project/black/>`_ to solve the problem once and for all.

- Fixers have to be registered with the :meth:`compat_patcher_core.PatchingRegistry.register_compatibility_fixer()` method of a patching registry. Hint: you can be DRY by using :code:`functools.partial` to preconfigure a set of similar fixers.

- Fixers must have a docstring explaining what they do (what breaking changes it deals with), and tests checking that both old and new behaviour keep working.

- Fixers should have a signature following the convention :code:`fix_<kind>_<path>_<element>(utils)`, where:

  - :code:`<kind>` is one of the following:

    - "deletion" (when an elemnt was removed from sources and must be put back).
    - "behavior" (when a signature changed, when an optional arguments became mandatory...).
    - "outsourcing" (when a whole submodule was turned into an external python package).

  - :code:`<path>` is the trail of submodules leading to the patched elemnt (with dots replaced by underscores), **not** including the root module of the library
  - :code:`<element>` is the element to be patched ; for clarity you should use the same character casing as the real elemnt name
  - :code:`utils` is the injected parameter, which exposes patching utilities

- Fixers should not be created to modify project-level code, like framework settings, since these are supposed to be easily updatable by project maintainers.

- Fixers should not reintroduce code which raises security issues (like XSS attacks...), unless these fixers are OFF by default, deeply documented, and risks can be properly mitigated by project maintainers.

- Fixers should be coded very *defensively*, since they are highly expected to repair breakages, not introduce new ones.

- Fixers should follow these rules of good behaviour:

  - Use monkey-patching utilities from the injected :code:`utils` object, not direct assignments
  - Not do logging or warnings by themselves either, but use the injected :code:`utils` object once again (or a dedicated WarningsProxy instance)
  - Not do global imports of software submodules or external libraries, but import them locally inside the fixer function





Testing fixers
--------------------

You can run :code:`python setup.py test`, which will install test requirements in a temporary folder, and launch pytest.

You can also install all test requirements in your virtualenv via :code:`pip -r requirements.txt` and run :code:`pytest -vl`.

MOST IMPORTANTLY, to test cross-version compatibility of your changes, install and run the "tox" python tool from the root folder of the repository; and ensure that all combinations of Python and your to-be-patched framework are present in "tox.ini".

A Travis file is included for Continuous Integration of your Git repository.
