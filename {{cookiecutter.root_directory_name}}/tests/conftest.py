def pytest_collection_modifyitems(config, items):
    from {{ cookiecutter.project_slug }}.registry import patching_registry
    from compat_patcher_core.scaffolding import (
        ensure_all_fixers_have_a_test_under_pytest,
    )

    ensure_all_fixers_have_a_test_under_pytest(
        config=config, items=items, patching_registry=patching_registry
    )
