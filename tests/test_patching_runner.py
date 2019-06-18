import dummy_module
from compat_patcher_core import (
    generic_patch_software,
    PatchingRegistry,
    DEFAULT_SETTINGS,
    make_safe_patcher,
)
from compat_patcher_core.registry import MultiPatchingRegistry
from compat_patcher_core.runner import PatchingRunner
from compat_patcher_core.utilities import PatchingUtilities, WarningsProxy
from dummy_fixers import patching_registry, patching_registry_bis


def test_runner_patch_software():

    PatchingRunner._clear_all_applied_fixers()  # Important

    del dummy_module.APPLIED_FIXERS[:]
    settings = DEFAULT_SETTINGS.copy()

    patching_utilities = PatchingUtilities(settings=settings)

    patching_runner = PatchingRunner(
        settings=settings,
        patching_utilities=patching_utilities,
        patching_registry=patching_registry,
    )

    _sorted_fixers_ids = [
        f["fixer_id"] for f in patching_runner._get_sorted_relevant_fixers()
    ]
    assert (
        "fix_something_but_skipped" in _sorted_fixers_ids
    )  # Will be aborted below during execution of fixers

    result = patching_runner.patch_software()
    # Fixers sorted by descending reference version and name
    assert result == dict(
        fixers_just_applied=[
            "fix_something_upto_v6",
            "fix_something_from_v5",
            "fix_something_always",
            "fix_something_from_v4",
        ]
    )

    assert (
        dummy_module.APPLIED_FIXERS == result["fixers_just_applied"]
    )  # Fixers are really run

    result = patching_runner.patch_software()
    assert result == dict(fixers_just_applied=[])  # Already applied so skipped

    patching_runner2 = PatchingRunner(
        settings=settings,
        patching_utilities=patching_utilities,
        patching_registry=patching_registry,
    )
    result = patching_runner2.patch_software()
    assert result == dict(
        fixers_just_applied=[]
    )  # Already applied so skipped, despite different runner instance


def test_generic_patch_software():

    PatchingRunner._clear_all_applied_fixers()  # Important

    del dummy_module.APPLIED_FIXERS[:]
    settings = DEFAULT_SETTINGS.copy()

    patching_registry_internal = PatchingRegistry(
        family_prefix="internal", current_software_version=lambda: "100"
    )

    @patching_registry_internal.register_compatibility_fixer(
        fixer_reference_version="8.3"
    )
    def fix_stuffs_internal(utils):
        "Does something still"
        assert utils.emit_log  # proper utility
        dummy_module.APPLIED_FIXERS.append(fix_stuffs_internal.__name__)

    warnings_proxy = WarningsProxy()
    assert not warnings_proxy._patching_utilities
    assert not patching_registry_internal._is_populated

    generic_patch_software(
        settings=settings,
        patching_registry=patching_registry_internal,
        warnings_proxy=warnings_proxy,
    )

    assert warnings_proxy._patching_utilities
    assert patching_registry_internal._is_populated
    assert dummy_module.APPLIED_FIXERS == ["fix_stuffs_internal"]


def test_fixer_idempotence_through_runner():

    PatchingRunner._clear_all_applied_fixers()  # Important

    del dummy_module.APPLIED_FIXERS[:]
    settings = DEFAULT_SETTINGS.copy()

    patching_utilities = PatchingUtilities(settings=settings)

    multi_registry = MultiPatchingRegistry(
        registries=[patching_registry, patching_registry_bis]
    )
    relevant_fixers = multi_registry.get_relevant_fixer_ids()
    assert relevant_fixers == [
        "fix_something_from_v4",
        "fix_something_from_v5",
        "fix_something_upto_v6",
        "fix_something_always",
        "fix_something_but_skipped",
        "fix_something_other_taken",
        "fix_something_always",  # This one is TWICE there, under different registries
    ]

    patching_runner2 = PatchingRunner(
        settings=settings,
        patching_utilities=patching_utilities,
        patching_registry=multi_registry,
    )
    result = patching_runner2.patch_software()
    assert result == dict(
        fixers_just_applied=[
            "fix_something_always",
            "fix_something_other_taken",
            "fix_something_upto_v6",
            "fix_something_from_v5",
            "fix_something_always",  # Properly run even if duplicate fixer_id
            "fix_something_from_v4",
        ]
    )


def test_make_safe_patcher():
    import time, threading

    shared_value = [0]

    @make_safe_patcher
    def slow_func(myattr):
        """
        This is a slooooow function.
        """
        value = shared_value[0]
        time.sleep(0.01)
        shared_value[0] = value + 1

    assert "slooooow" in slow_func.__doc__  # Properly wrapped

    threads = [
        threading.Thread(target=slow_func, kwargs=dict(myattr=22)) for i in range(5)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert shared_value[0] == 5
