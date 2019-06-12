

import dummy_module
from compat_patcher.exceptions import SkipFixerException

from compat_patcher.registry import PatchingRegistry

patching_registry = PatchingRegistry(family_prefix="dummy")


@patching_registry.register_compatibility_fixer(fixer_reference_version="4.0",
                                              fixer_applied_from_version="4.0",
                                              fixer_applied_upto_version="9.3",
                                              fixer_tags=[])
def fix_something_from_v4(utils):
    "Does something here"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v4.__name__)
    return 22
assert fix_something_from_v4(utils=33) == 22  # Decorator doesn't erase wrapped function


@patching_registry.register_compatibility_fixer(fixer_reference_version="5.0",
                                              fixer_applied_from_version="5.0",
                                              fixer_tags=["mytag"])
def fix_something_from_v5(utils):
    "Does something there"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v5.__name__)


@patching_registry.register_compatibility_fixer(fixer_reference_version="5.0",
                                              fixer_applied_from_version="4.2",
                                              fixer_applied_upto_version="6.0")
def fix_something_upto_v6(utils):
    "Does something again"
    dummy_module.APPLIED_FIXERS.append(fix_something_upto_v6.__name__)


@patching_registry.register_compatibility_fixer(fixer_reference_version="5.0")
def fix_something_always(utils):
    "Does something always"
    dummy_module.APPLIED_FIXERS.append(fix_something_always.__name__)


@patching_registry.register_compatibility_fixer(fixer_reference_version="5.0")
def fix_something_but_skipped(utils):
    "Does something always"
    raise SkipFixerException("Fixer fix_something_but_skipped is always skipped")



@patching_registry.register_compatibility_fixer(fixer_reference_version="6.0",
                                              fixer_applied_from_version="6.0",
                                              feature_supported_upto_version="6.5")
def fix_something_from_v6(utils):
    "Does something bis"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v6.__name__)



@patching_registry.register_compatibility_fixer(fixer_reference_version="6.3",
                                              fixer_applied_from_version="7.3",
                                              feature_supported_from_version="5.0",
                                              feature_supported_upto_version="11.2")
def fix_something_from_v7(utils):
    "Does something still"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v7.__name__)


