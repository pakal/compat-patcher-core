API
==================


Patching launcher
--------------------

Each package implementing a compat-patcher for a specific framework/library should expose a `patch()` function
at the top level, responsible for the whole process of retrieving configuration, instantiating miscellaneous utilities,
selecting relevant fixers, and applying them.

**These building blocks are exposed to ease the process fo creating this launcher.**

.. autofunction:: compat_patcher_core.generic_patch_software

.. autofunction:: compat_patcher_core.make_safe_patcher


Patching registry
-------------------


.. autoclass:: compat_patcher_core.PatchingRegistry
    :members:

.. autoclass:: compat_patcher_core.MultiPatchingRegistry
    :members:


Patching utilities
--------------------

.. autoclass:: compat_patcher_core.PatchingUtilities
    :members:

    .. autoattribute:: settings_keys_used

.. autoclass:: compat_patcher_core.WarningsProxy

.. autofunction:: compat_patcher_core.tuplify_software_version

.. autofunction:: compat_patcher_core.detuplify_software_version


Patching runner
-------------------

.. autoclass:: compat_patcher_core.PatchingRunner
    :members:


Patching exceptions
---------------------

.. autoclass:: compat_patcher_core.SkipFixerException


Patching configuration
---------------------------

The `settings` expected by classes above must be a dict-like object (just a __getitem__() method is enough), which raises KeyError if a setting is not found.

.. autodata:: compat_patcher_core.DEFAULT_SETTINGS
