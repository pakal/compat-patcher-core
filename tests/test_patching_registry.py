from __future__ import absolute_import, print_function, unicode_literals

import functools

import pytest

from compat_patcher_core.registry import PatchingRegistry, MultiPatchingRegistry
from dummy_fixers import patching_registry, patching_registry_bis, patching_registry_ter


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

    fixer_ids_v5 = (
        get_relevant_fixer_ids()
    )  # current_software_version defaults to registry's value
    assert set(fixer_ids_v5) == set(
        [
            "fix_something_from_v4",
            "fix_something_from_v5",
            "fix_something_upto_v6",
            "fix_something_always",
            "fix_something_but_skipped",
        ]
    )
    assert len(patching_registry.get_relevant_fixers()) == 5  # Same

    fixer_ids = get_relevant_fixer_ids(current_software_version="5.0", qualified=True)
    assert set(fixer_ids) == set(
        [
            "dummy4.0|fix_something_from_v4",
            "dummy5.0|fix_something_from_v5",
            "dummy5.0|fix_something_upto_v6",
            "dummy5.0|fix_something_always",
            "dummy5.0|fix_something_but_skipped",
        ]
    )

    fixer_ids = get_relevant_fixer_ids(current_software_version="5.0")
    assert set(fixer_ids) == set(
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
        include_fixer_ids=["dummy4.0|fix_something_from_v4"],
        include_fixer_families=["dummy5.0"],
        exclude_fixer_ids=["dummy5.0|fix_something_always"],
    )
    fixer_ids = get_relevant_fixer_ids(
        current_software_version="5.5.4", qualified=True, **fixer_settings
    )
    assert set(fixer_ids) == set(
        [
            "dummy4.0|fix_something_from_v4",
            "dummy5.0|fix_something_from_v5",
            "dummy5.0|fix_something_upto_v6",
            "dummy5.0|fix_something_but_skipped",
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
    registry = PatchingRegistry(
        family_prefix="dummy2", current_software_version=lambda: AAA
    )
    with pytest.raises(NameError):
        registry._get_current_software_version()

    registry = PatchingRegistry(
        family_prefix="dummy3", current_software_version=lambda: (1, 2, 3)
    )
    assert registry._get_current_software_version() == (1, 2, 3)

    registry = PatchingRegistry(
        family_prefix="dummy4", current_software_version="8.2.1"
    )
    assert registry._get_current_software_version() == "8.2.1"

    registry = PatchingRegistry(family_prefix="dummy5")
    assert registry._get_current_software_version() is None
    with pytest.raises(ValueError, match="valid current_software_version"):
        registry.get_relevant_fixers()
    assert registry.get_relevant_fixers(current_software_version="1") == []


def test_multi_patching_registry():

    multi_registry = MultiPatchingRegistry(
        registries=[patching_registry, patching_registry_bis]
    )
    assert not patching_registry_bis._is_populated
    assert not multi_registry._is_populated

    assert len(patching_registry.get_all_fixers()) == 7
    assert len(patching_registry_bis.get_all_fixers()) == 3

    fixers = multi_registry.get_all_fixers()
    assert len(fixers) == 10  # All, including duplicate names!
    assert not patching_registry_bis._is_populated
    assert not multi_registry._is_populated

    fixer = multi_registry.get_fixer_by_id("fix_something_always")
    assert fixer["fixer_reference_version"] == (5, 0)  # First one is returned!
    with pytest.raises(KeyError):
        multi_registry.get_fixer_by_id("badname")
    assert not patching_registry_bis._is_populated
    assert not multi_registry._is_populated

    selected_fixers = multi_registry.get_relevant_fixer_ids()
    assert selected_fixers == [
        "fix_something_from_v4",
        "fix_something_from_v5",
        "fix_something_upto_v6",
        "fix_something_always",
        "fix_something_but_skipped",
        "fix_something_other_taken",
        "fix_something_always",
    ]  # Duplicate fixer is taken too
    assert patching_registry_bis._is_populated
    assert multi_registry._is_populated

    misc_fixers = multi_registry.get_relevant_fixer_ids(current_software_version="1000")
    assert misc_fixers == [
        "fix_something_from_v5",
        "fix_something_always",
        "fix_something_but_skipped",
        "fix_something_from_v6",
        "fix_something_from_v7",
        "fix_something_other_taken",
        "fix_something_other_not_taken",
        "fix_something_always",
    ]

    multi_registry2 = MultiPatchingRegistry(
        registries=[
            "dummy_fixers.patching_registry_bis",
            "dummy_fixers.patching_registry_ter_as_callable",
        ]
    )
    assert not multi_registry2._is_populated
    assert not patching_registry_ter._is_populated

    multi_registry2.populate()
    assert multi_registry2._is_populated
    assert patching_registry_ter._is_populated

    selected_fixers2 = multi_registry2.get_relevant_fixer_ids()

    assert selected_fixers2 == [
        "fix_something_other_taken",
        "fix_something_always",
        "fix_everything",
    ]

    with pytest.raises(ValueError, match="Wrong registry reference"):
        MultiPatchingRegistry(registries=["dummy_fixers.SkipFixerException"])

    with pytest.raises(ImportError):
        MultiPatchingRegistry(registries=["badmodule.unexisting"])

    with pytest.raises(AttributeError):
        MultiPatchingRegistry(registries=["dummy_fixers.unexisting"])

    with pytest.raises(ValueError, match="unpack"):
        MultiPatchingRegistry(registries=["badstring"])
