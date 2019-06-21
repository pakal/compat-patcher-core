from __future__ import absolute_import, print_function, unicode_literals

import os

import _test_utilities


def test_fix_behaviour_submodule_element():
    import my_import_alias_for_csv
    del my_import_alias_for_csv  # All worked!
