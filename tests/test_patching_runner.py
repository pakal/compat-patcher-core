from compat_patcher.runner import PatchingRunner

'''


class MyPatchingRunner(PatchingRunner):

    forced_software_version = "5.0"

    def _get_software_version(self):
        return self.forced_software_version


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
