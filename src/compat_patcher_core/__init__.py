import threading as _threading

from .exceptions import SkipFixerException
from .registry import PatchingRegistry, MultiPatchingRegistry
from .runner import PatchingRunner
from .utilities import (
    PatchingUtilities,
    WarningsProxy,
    tuplify_software_version,
    detuplify_software_version,
)


def generic_patch_software(
    settings,
    patching_registry,
    patching_utilities_class=PatchingUtilities,
    patching_runner_class=PatchingRunner,
    warnings_proxy=None,
):
    """Load all dependencies, and apply relevant fixers from the `patching_registry`,
    according to the settings of the provided `settings`.

    You can provide custom classes to be instantiated instead of default ones, and/or an
    existing WarningsProxy which will be updated with the new settings as soon as possible.
    """

    patching_registry.populate()
    assert patching_registry._is_populated

    patching_utilities = patching_utilities_class(settings=settings)

    if warnings_proxy:  # Update the config of preexisting WarningsProxy
        warnings_proxy.set_patching_utilities(patching_utilities)

    patching_runner = patching_runner_class(
        settings=settings,
        patching_utilities=patching_utilities,
        patching_registry=patching_registry,
    )
    patching_runner.patch_software()

    return None  # No return value for now, if some is set one day it shall be a DICT!


#: Example configuration to copy() and adapt
DEFAULT_SETTINGS = dict(
    logging_level="INFO",
    enable_warnings=True,
    patch_injected_objects=True,
    include_fixer_ids="*",
    include_fixer_families=None,
    exclude_fixer_ids=None,
    exclude_fixer_families=None,
)


#: Lock meant to globally protect all the patching workflow
PATCHING_LOCK = _threading.RLock()


def make_safe_patcher(f):
    """
    This decorator makes a patching launcher thread-safe with a recursive lock.

    Other checks and misc. features might be added in the future, so packages using
    this patching framework should always decorate their main "patch()" entrypoint
    with this utility.
    """
    import functools

    @functools.wraps(f)
    def inner(*args, **kwargs):
        with PATCHING_LOCK:
            return f(*args, **kwargs)

    return inner
