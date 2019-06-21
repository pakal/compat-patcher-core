from __future__ import absolute_import, print_function, unicode_literals

from compat_patcher_core.registry import PatchingRegistry


def populate_fixers_registry(registry):
    from . import fixers


# TODO fetch and return the real version of the patched framework/library
def get_current_software_version():
    return "1.2.3"


# This must be instantiated HERE so that fixer submodules can access it at import time
patching_registry = PatchingRegistry(
    family_prefix="{{ cookiecutter.project_prefix }}",
    populate_callable=populate_fixers_registry,
    current_software_version=get_current_software_version,
)

register_compatibility_fixer = (
    patching_registry.register_compatibility_fixer
)  # Shortcut









