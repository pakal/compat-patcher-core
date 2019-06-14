from __future__ import absolute_import, print_function, unicode_literals

import functools

import pytest

from compat_patcher.registry import PatchingRegistry
from dummy_fixers import patching_registry


def test_registry_populate():

    assert patching_registry.populate() is None  # Nothing done
    assert patching_registry.populate() is None  # Again

    registry = PatchingRegistry("dummyfamily", populate_callable=lambda registry: XYZ)
    with pytest.raises(NameError):
        registry.populate()

    registry = PatchingRegistry(
        "dummyfamily2", populate_callable=lambda registry: registry
    )
    assert registry.populate() is registry
    assert registry.populate() is None  # Idempotent


def test_get_relevant_fixer_ids():
    def log(msg):
        print(msg)

    get_relevant_fixer_ids = functools.partial(
        patching_registry.get_relevant_fixer_ids, log=log
    )

    assert patching_registry._get_current_software_version() == "5.1"

    fixer_ids_v5 = get_relevant_fixer_ids()  # current_software_version defaults to registry's value
    assert set(fixer_ids_v5) == set(
        [
            "fix_something_from_v4",
            "fix_something_from_v5",
            "fix_something_upto_v6",
            "fix_something_always",
            "fix_something_but_skipped",
        ]
    )

    fixer_ids_v5 = get_relevant_fixer_ids(current_software_version="5.0")
    assert set(fixer_ids_v5) == set(
        [
            "fix_something_from_v4",
            "fix_something_from_v5",
            "fix_something_upto_v6",
            "fix_something_always",
            "fix_something_but_skipped",
        ]
    )

    fixer_ids = get_relevant_fixer_ids(current_software_version="2.2")
    assert set(fixer_ids) == set(["fix_something_always", "fix_something_but_skipped"])

    fixer_ids = get_relevant_fixer_ids(current_software_version="10")
    assert set(fixer_ids) == set(
        [
            "fix_something_from_v5",
            "fix_something_from_v6",
            "fix_something_from_v7",
            "fix_something_always",
            "fix_something_but_skipped",
        ]
    )

    fixer_ids = get_relevant_fixer_ids(current_software_version="6.0")
    assert set(fixer_ids) == set(
        [
            "fix_something_from_v4",
            "fix_something_from_v5",
            "fix_something_from_v6",
            "fix_something_always",
            "fix_something_but_skipped",
        ]
    )  # But not "upto v6"

    fixer_settings = dict(
        include_fixer_ids=None,
        include_fixer_families=None,
        exclude_fixer_ids=None,
        exclude_fixer_families=None,
    )
    fixer_ids = get_relevant_fixer_ids(current_software_version="5.0", **fixer_settings)
    assert not fixer_ids

    fixer_settings = dict(
        include_fixer_ids=[],
        include_fixer_families=["dummy4.0"],
        exclude_fixer_ids=[],
        exclude_fixer_families=[],
    )
    fixer_ids = get_relevant_fixer_ids(current_software_version="5.0", **fixer_settings)
    assert set(fixer_ids) == set(["fix_something_from_v4"])

    fixer_settings = dict(
        include_fixer_ids="*",
        include_fixer_families=None,
        exclude_fixer_ids=[],
        exclude_fixer_families=[],
    )
    fixer_ids = get_relevant_fixer_ids(current_software_version="5.0", **fixer_settings)
    assert set(fixer_ids) == set(fixer_ids_v5)

    fixer_settings = dict(
        include_fixer_ids=[],
        include_fixer_families="*",
        exclude_fixer_ids=None,
        exclude_fixer_families=[],
    )
    fixer_ids = get_relevant_fixer_ids(current_software_version="5.0", **fixer_settings)
    assert set(fixer_ids) == set(fixer_ids_v5)

    fixer_settings = dict(
        include_fixer_ids=["fix_something_from_v4"],
        include_fixer_families=["dummy5.0"],
        exclude_fixer_ids=["fix_something_upto_v6"],
        exclude_fixer_families=None,
    )
    fixer_ids = get_relevant_fixer_ids(
        current_software_version="5.5.4", **fixer_settings
    )
    assert set(fixer_ids) == set(
        [
            "fix_something_from_v4",
            "fix_something_from_v5",
            "fix_something_always",
            "fix_something_but_skipped",
        ]
    )

    fixer_settings = dict(
        include_fixer_ids=["fix_something_from_v4"],
        include_fixer_families=["dummy5.0"],
        exclude_fixer_ids=["unexisting_id"],
        exclude_fixer_families=["dummy4.0"],
    )
    fixer_ids = get_relevant_fixer_ids(
        current_software_version="5.5.4", **fixer_settings
    )
    assert set(fixer_ids) == set(
        [
            "fix_something_from_v5",
            "fix_something_upto_v6",
            "fix_something_always",
            "fix_something_but_skipped",
        ]
    )

    fixer_settings = dict(
        include_fixer_ids=["fix_something_from_v4"],
        include_fixer_families=["dummy5.0"],
        exclude_fixer_ids=[],
        exclude_fixer_families="*",
    )
    fixer_ids = get_relevant_fixer_ids(
        current_software_version="5.5.4", **fixer_settings
    )
    assert fixer_ids == []

    fixer_settings = dict(
        include_fixer_ids="*",
        include_fixer_families=["dummy5.0"],
        exclude_fixer_ids="*",
        exclude_fixer_families=None,
    )
    fixer_ids = get_relevant_fixer_ids(
        current_software_version="5.5.4", **fixer_settings
    )
    assert fixer_ids == []


def test_get_fixer_by_id():
    res = patching_registry.get_fixer_by_id("fix_something_from_v7")
    assert isinstance(res, dict)
    assert res["fixer_id"] == "fix_something_from_v7"

    with pytest.raises(KeyError):
        patching_registry.get_fixer_by_id("ddssdfsdfsdf")


def test_get_all_fixers():
    res = patching_registry.get_all_fixers()
    assert len(res) == 7


def test_docstring_mandatory_on_fixers():
    with pytest.raises(ValueError):

        @patching_registry.register_compatibility_fixer(
            fixer_reference_version="5.0", fixer_applied_from_version="6.0"
        )
        def fixer_without_docstring(utils):
            pass

def test_registry_current_software_version():
    registry = PatchingRegistry(family_prefix="dummy2",
                              current_software_version=lambda: AAA)
    with pytest.raises(NameError):
        registry._get_current_software_version()

    registry = PatchingRegistry(family_prefix="dummy3",
                              current_software_version=lambda: (1, 2, 3))
    assert registry._get_current_software_version() == (1, 2, 3)

    registry = PatchingRegistry(family_prefix="dummy4",
                              current_software_version="8.2.1")
    assert registry._get_current_software_version() == "8.2.1"

    registry = PatchingRegistry(family_prefix="dummy5")
    assert registry._get_current_software_version() is None
    with pytest.raises(ValueError, match="valid current_software_version"):
        registry.get_relevant_fixers()
    assert registry.get_relevant_fixers(current_software_version="1") == []
