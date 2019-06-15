import dummy_module
from compat_patcher import generic_patch_software, PatchingRegistry
from compat_patcher.registry import MultiPatchingRegistry
from compat_patcher.runner import PatchingRunner
from compat_patcher.utilities import PatchingUtilities, WarningsProxy
from dummy_fixers import patching_registry, patching_registry_ter, patching_registry_bis

CONFIG_PROVIDER_EXAMPLE = dict(
    logging_level="DEBUG",
    enable_warnings=True,
    patch_injected_objects=True,
    include_fixer_ids="*",
    include_fixer_families=None,
    exclude_fixer_ids=None,
    exclude_fixer_families=None,
)


def test_runner_patch_software():

    PatchingRunner._clear_all_applied_fixers()  # Important

    del dummy_module.APPLIED_FIXERS[:]
    config_provider = CONFIG_PROVIDER_EXAMPLE.copy()

    patching_utilities = PatchingUtilities(config_provider=config_provider)

    django_patching_runner = PatchingRunner(
        config_provider=config_provider,
        patching_utilities=patching_utilities,
        patching_registry=patching_registry,
    )

    _sorted_fixers_ids = [
        f["fixer_id"] for f in django_patching_runner._get_sorted_relevant_fixers()
    ]
    assert (
        "fix_something_but_skipped" in _sorted_fixers_ids
    )  # Will be aborted below during execution of fixers

    fixers_applied = django_patching_runner.patch_software()
    # Fixers sorted by descending reference version and name
    assert fixers_applied == [
        "fix_something_upto_v6",
        "fix_something_from_v5",
        "fix_something_always",
        "fix_something_from_v4",
    ]

    assert dummy_module.APPLIED_FIXERS == fixers_applied  # Fixers are really run

    fixers_applied = django_patching_runner.patch_software()
    assert fixers_applied == []  # Already applied so skipped

    django_patching_runner2 = PatchingRunner(
        config_provider=config_provider,
        patching_utilities=patching_utilities,
        patching_registry=patching_registry,
    )
    fixers_applied = django_patching_runner2.patch_software()
    assert (
        fixers_applied == []
    )  # Already applied so skipped, despite different runner instance


def test_generic_patch_software():

    PatchingRunner._clear_all_applied_fixers()  # Important

    del dummy_module.APPLIED_FIXERS[:]
    config_provider = CONFIG_PROVIDER_EXAMPLE.copy()

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
        config_provider=config_provider,
        patching_registry=patching_registry_internal,
        warnings_proxy=warnings_proxy,
    )

    assert warnings_proxy._patching_utilities
    assert patching_registry_internal._is_populated
    assert dummy_module.APPLIED_FIXERS == ["fix_stuffs_internal"]


def test_fixer_idempotence_through_runner():

    PatchingRunner._clear_all_applied_fixers()  # Important

    del dummy_module.APPLIED_FIXERS[:]
    config_provider = CONFIG_PROVIDER_EXAMPLE.copy()

    patching_utilities = PatchingUtilities(config_provider=config_provider)

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

    django_patching_runner2 = PatchingRunner(
        config_provider=config_provider,
        patching_utilities=patching_utilities,
        patching_registry=multi_registry,
    )
    just_applied_fixers = django_patching_runner2.patch_software()
    assert just_applied_fixers == [
        "fix_something_always",
        "fix_something_other_taken",
        "fix_something_upto_v6",
        "fix_something_from_v5",
        "fix_something_always",  # Properly run even if duplicate fixer_id
        "fix_something_from_v4",
    ]
