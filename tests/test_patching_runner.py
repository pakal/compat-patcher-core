
import pytest
from compat_patcher.utilities import PatchingUtilities
from compat_patcher.runner import PatchingRunner

import dummy_module
from dummy_fixers import patching_registry

class ____MyPatchingRunner(PatchingRunner):

    forced_software_version = "5.0"

    def _get_software_version(self):
        return self.forced_software_version





def test_patch_software():
    """Load every dependency, and apply registered fixers according to provided settings (or Django settings as a fallback)."""

    del dummy_module.APPLIED_FIXERS[:]

    config_provider = dict(logging_level="DEBUG",
                           enable_warnings=True,
                           patch_injected_objects=True,
                           include_fixer_ids = "*",
                           include_fixer_families = None,
                            exclude_fixer_ids = None,
                            exclude_fixer_families=None)

    patching_utilities = PatchingUtilities(config_provider=config_provider)

    django_patching_runner = PatchingRunner(config_provider=config_provider,
                                              patching_utilities=patching_utilities,
                                              patching_registry=patching_registry,
                                            current_software_version="5.0")

    _sorted_fixers_ids = [f["fixer_id"] for f in django_patching_runner._get_sorted_relevant_fixers()]
    assert "fix_something_but_skipped" in _sorted_fixers_ids  # Will be aborted below during execution of fixers

    fixers_applied = django_patching_runner.patch_software()
    # Fixers sorted by descending reference version and name
    assert fixers_applied == ['fix_something_upto_v6', 'fix_something_from_v5', 'fix_something_always', 'fix_something_from_v4']

    assert dummy_module.APPLIED_FIXERS == fixers_applied  # Fixers are really run

    fixers_applied = django_patching_runner.patch_software()
    assert fixers_applied == []  # Already applied so skipped


    with pytest.raises(ValueError, match="valid current_software_version"):
        django_patching_runner = PatchingRunner(config_provider=config_provider,
                                                  patching_utilities=patching_utilities,
                                                  patching_registry=patching_registry,
                                                )
        django_patching_runner.patch_software()


'''




def patch(settings=None):
    """Load every dependency, and apply registered fixers according to provided settings (or Django settings as a fallback)."""

    from .config import DjangoConfigProvider
    from .utilities import DjangoPatchingUtilities
    from .registry import DjangoPatchingRegistry
    from .runner import DjangoPatchingRunner

    config_provider = DjangoConfigProvider(settings=settings)

    patching_utilities = DjangoPatchingUtilities(config_provider=config_provider)

    from . import deprecation  # Immediately finish setting up this module
    deprecation.warnings.set_patching_utilities(patching_utilities)

    from . import fixers  # Force-load every fixer submodule
    from .registry import django_patching_registry

    django_patching_runner = DjangoPatchingRunner(config_provider=config_provider,
                                                  patching_utilities=patching_utilities,
                                                  patching_registry=django_patching_registry,)
    django_patching_runner.patch_software()

'''
