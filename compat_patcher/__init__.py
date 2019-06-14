from .exceptions import SkipFixerException
from .registry import PatchingRegistry
from .runner import PatchingRunner
from .utilities import PatchingUtilities, WarningsProxy


def generic_patch_software(
    config_provider,
    patching_registry,
    patching_utilities_class=PatchingUtilities,
    patching_runner_class=PatchingRunner,
    warnings_proxy=None,
):
    """Load all dependencies, and apply registered fixers according to provided config.

    You can pass custom classes to be instantiated, and/or an existing WarningsProxy which will be updated
    with the new config as soon as possible.
    """

    patching_registry.populate()
    assert patching_registry._is_populated

    patching_utilities = patching_utilities_class(config_provider=config_provider)

    if warnings_proxy:  # Update the config of preexisting WarningsProxy
        warnings_proxy.set_patching_utilities(patching_utilities)

    django_patching_runner = patching_runner_class(
        config_provider=config_provider,
        patching_utilities=patching_utilities,
        patching_registry=patching_registry,
    )
    django_patching_runner.patch_software()
