API
#################

Patching launcher
===================

.. autofunction:: compat_patcher.generic_patch_software

.. autofunction:: compat_patcher.make_safe_patcher


Patching registry
=========================


.. autoclass:: compat_patcher.PatchingRegistry
    :members:

.. autoclass:: compat_patcher.MultiPatchingRegistry
    :members:


Patching utilities
=========================

.. autoclass:: compat_patcher.PatchingUtilities
    :members:

    .. autoattribute:: config_keys_used

.. autoclass:: compat_patcher.WarningsProxy

.. autofunction:: compat_patcher.tuplify_software_version

.. autofunction:: compat_patcher.detuplify_software_version


Patching runner
=========================

.. autoclass:: compat_patcher.PatchingRunner
    :members:

Patching exceptions
=========================

.. autoclass:: compat_patcher.SkipFixerException

Patching configuration
=========================

The `config_provider` expected by the classes above must be a dict-like object (just a __getitem__() method is enough), which raises KeyError if a setting is not found.

.. autodata:: compat_patcher.DEFAULT_CONFIG
