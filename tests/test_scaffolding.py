import os

import pytest

import compat_patcher_core
from compat_patcher_core import PatchingRegistry
from compat_patcher_core.scaffolding import (
    ensure_no_stdlib_warnings,
    ensure_all_fixers_have_a_test_under_pytest,
)


def test_ensure_all_fixers_have_a_test_under_pytest():
    class DummyNode:
        pass

    patching_registry = PatchingRegistry("dummyname")

    @patching_registry.register_compatibility_fixer(fixer_reference_version="10.1")
    def my_dummy_fixer(utils):
        "A help string"
        pass

    node = DummyNode()
    node.name = "test_my_dummy_fixer"
    items = [node]

    # No problem, all registered fixers have their test here
    ensure_all_fixers_have_a_test_under_pytest(
        config=None, items=items, patching_registry=patching_registry, _fail_fast=True
    )

    # Error when attempting to clone first item to report the missing test
    with pytest.raises(RuntimeError, match="No test written for .* fixer"):
        ensure_all_fixers_have_a_test_under_pytest(
            config=None, items=[], patching_registry=patching_registry, _fail_fast=True
        )


def test_ensure_no_stdlib_warnings_in_package():
    import warnings  # This line will trigger checker error

    del warnings
    pkg_root = os.path.dirname(compat_patcher_core.__file__)
    analysed_files = ensure_no_stdlib_warnings(pkg_root)
    assert len(analysed_files) > 5, analysed_files

    test_root = os.path.dirname(__file__)
    with pytest.raises(ValueError, match="wrong phrase.*test_scaffolding.py"):
        ensure_no_stdlib_warnings(test_root)


def test_no_package_shadowing_in_tox():
    import compat_patcher_core

    package_dir = os.path.dirname(os.path.abspath(compat_patcher_core.__file__))
    if os.getenv("INSIDE_TOX_FOR_CPC") and ".tox" not in package_dir:
        raise RuntimeError("Wrong compat_patcher_core package used in Tox")
