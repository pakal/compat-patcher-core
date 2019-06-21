from __future__ import absolute_import, print_function, unicode_literals

# Use this this to preconfigure "register_compatibility_fixer" for a set of fixers
from functools import partial

from ..deprecation import *
from ..registry import register_compatibility_fixer


@register_compatibility_fixer(
        fixer_reference_version="1.0",
        fixer_applied_from_version="1.0"
)
def fix_behaviour_submodule_element(utils):
    """Help string is mandatory to explain what the fixer does! Here, something..."""
    utils.emit_warning("Something was deprecated in software", DeprecationWarning)
    utils.inject_import_alias(alias_name="my_import_alias_for_csv", real_name="csv")
    # HERE use injectors from utils to modify the software
