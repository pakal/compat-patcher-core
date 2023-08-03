Guidelines for writing fixers
===========================================

compat_patcher_core.PatchingRegistry.

- Follow PEP8 as much as you can, or use `Black <https://pypi.org/project/black/>`_ to solve the problem once and for all.

- Fixers have to be registered with the :meth:`.register_compatibility_fixer()` method of a patching registry. Hint: you can be DRY by using :code:`functools.partial()` to preconfigure a set of similar fixers.

- Fixers must have a docstring explaining what they do (what breaking changes they deal with), and tests checking that both old and new behaviour keep working. These tests must have a name matching the form "test_<fixer-name>()" to be recognized.

- Fixers should have a signature following the convention :code:`fix_<kind>_<path>_<element>(utils)`, where:

  - :code:`<kind>` is one of the following:

    - "deletion" (when an element was removed from sources and must be put back)
    - "behavior" (when a signature changed, when an optional arguments became mandatory...)
    - "outsourcing" (when a whole submodule was turned into an external python package)

  - :code:`<path>` is the trail of submodules leading to the patched element (with dots replaced by underscores), **not** including the root module of the library
  - :code:`<element>` is the element to be patched ; for clarity you should use the same character casing as the real element name
  - :code:`utils` is the injected parameter, which exposes patching utilities

- Fixers should be coded quite *defensively*, since they are highly expected to repair breakages, not introduce new ones.

- Fixers should follow these rules of good behaviour:

  - Use monkey-patching utilities from the injected :code:`utils` object, not direct assignments
  - Not do logging or warnings by themselves either, but use the injected :code:`utils` object once again (or a dedicated WarningsProxy instance)
  - Not do global imports of software submodules or external libraries, but import them *locally* inside the fixer function

- Fixers should not reintroduce code which raises security issues (like XSS attacks...), unless these fixers are OFF by default, deeply documented, and risks can be properly mitigated by project maintainers.

- Fixers should not be created to modify project-level code, like framework settings, since these are supposed to be easily updatable by project maintainers.




