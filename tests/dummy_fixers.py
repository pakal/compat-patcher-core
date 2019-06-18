import os

import compat_patcher_core
import dummy_module
from compat_patcher_core.exceptions import SkipFixerException
from compat_patcher_core.registry import PatchingRegistry

# Important, when testing with Tox, we must ensure no shadowing occurs
PACKAGE_DIR = os.path.dirname(os.path.abspath(compat_patcher_core.__file__))
print(
    '### TESTING DUMMY FIXERS WITH THE COMPAT_PATCHER_CORE FROM "%s" ###' % PACKAGE_DIR
)


patching_registry = PatchingRegistry(
    family_prefix="dummy", current_software_version=lambda: "5.1"
)


@patching_registry.register_compatibility_fixer(
    fixer_reference_version="4.0",
    fixer_applied_from_version="4.0",
    fixer_applied_upto_version="9.3",
    fixer_tags=[],
)
def fix_something_from_v4(utils):
    "Does something here"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v4.__name__)
    return 22


assert fix_something_from_v4(utils=33) == 22  # Decorator doesn't erase wrapped function


@patching_registry.register_compatibility_fixer(
    fixer_reference_version="5.0",
    fixer_applied_from_version="5.0",
    fixer_tags=["mytag"],
)
def fix_something_from_v5(utils):
    "Does something there"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v5.__name__)


@patching_registry.register_compatibility_fixer(
    fixer_reference_version="5.0",
    fixer_applied_from_version="4.2",
    fixer_applied_upto_version="6.0",
)
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


@patching_registry.register_compatibility_fixer(
    fixer_reference_version="6.0",
    fixer_applied_from_version="6.0",
    feature_supported_upto_version="6.5",
)
def fix_something_from_v6(utils):
    "Does something bis"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v6.__name__)


@patching_registry.register_compatibility_fixer(
    fixer_reference_version="6.3",
    fixer_applied_from_version="7.3",
    feature_supported_from_version="5.0",
    feature_supported_upto_version="11.2",
)
def fix_something_from_v7(utils):
    "Does something still"
    dummy_module.APPLIED_FIXERS.append(fix_something_from_v7.__name__)


### -------------------

patching_registry_bis = PatchingRegistry(
    family_prefix="other", current_software_version=lambda: "10"
)


@patching_registry_bis.register_compatibility_fixer(
    fixer_reference_version="6.3", fixer_applied_from_version="7.3"
)
def fix_something_other_taken(utils):
    "Does something still"
    dummy_module.APPLIED_FIXERS.append(fix_something_other_taken.__name__)


@patching_registry_bis.register_compatibility_fixer(
    fixer_reference_version="6.3", fixer_applied_from_version="20"
)
def fix_something_other_not_taken(utils):
    "Does something still"
    dummy_module.APPLIED_FIXERS.append(fix_something_other_not_taken.__name__)


assert fix_something_always  # Already existing


def __fix_something_always(utils):
    "Does something still"
    dummy_module.APPLIED_FIXERS.append(__fix_something_always.__name__)


__fix_something_always.__name__ = "fix_something_always"

patching_registry_bis.register_compatibility_fixer(fixer_reference_version="8.3")(
    __fix_something_always
)

### -------------------

patching_registry_ter = PatchingRegistry(
    family_prefix="somefamily", current_software_version=lambda: "100"
)


@patching_registry_ter.register_compatibility_fixer(fixer_reference_version="8.3")
def fix_everything(utils):
    "Does something still"
    dummy_module.APPLIED_FIXERS.append(fix_everything.__name__)


patching_registry_ter_as_callable = lambda: patching_registry_ter
