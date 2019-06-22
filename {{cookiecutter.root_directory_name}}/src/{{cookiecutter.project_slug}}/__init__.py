# -*- coding: utf-8 -*-


from compat_patcher_core import generic_patch_software, make_safe_patcher, DEFAULT_SETTINGS


@make_safe_patcher
def patch(settings=None):

    # TODO replace this by default settings extracted from the patched framework
    settings = settings if settings is not None else DEFAULT_SETTINGS

    from .registry import patching_registry
    # Use the following import form to avoid triggering checker alerts on "warnings" import
    import {{ cookiecutter.project_slug }}.deprecation

    generic_patch_software(
        settings=settings,
        patching_registry=patching_registry,
        warnings_proxy=deprecation.warnings,
    )

