def ensure_no_stdlib_warnings(
    source_root,
    # we authorize "warnings.warn", as long as it uses the custom WarningsProxy above
    forbidden_phrases=("import " + "warnings", "from " + "warnings"),
):
    """
    This utility should be used by each compat patcher user, to ensure all shims only
    go through the configurable compat-patcher warnings system.

    Returns the list of checked python source files.
    """
    import os

    analysed_files = []

    for root, _subdirs, files in os.walk(source_root):
        for f in [x for x in files if x.endswith(".py")]:
            full_path = os.path.join(root, f)
            # print(">> ANALYSING PYTHON FILE", full_path)
            with open(full_path, "r") as s:
                data = s.read()
            for forbidden_phrase in forbidden_phrases:
                if forbidden_phrase in data:
                    if (f == "utilities.py") and (
                        "import " + "warnings as stdlib_warnings" in data
                    ):
                        continue  # the only case OK is our own warnings utility
                    raise ValueError(
                        "ALERT, wrong phrase '%s' detected in %s"
                        % (forbidden_phrase, full_path)
                    )
            analysed_files.append(f)
    return analysed_files


def ensure_all_fixers_have_a_test_under_pytest(
    config, items, patching_registry, _fail_fast=False
):
    """Call this pytest hook from a conftest.py to ensure your own test suite covers
    all your registered fixers, like so::

        def pytest_collection_modifyitems(config, items):
            from yourownpackage.registry import your_patching_registry
            from compat_patcher_core.test_scaffolding import ensure_all_fixers_have_a_test_under_pytest
            ensure_all_fixers_have_a_test_under_pytest(
                config=config, items=items, patching_registry=your_patching_registry
            )
    """
    import copy
    from _pytest.python import Function

    all_fixers = patching_registry.get_all_fixers()
    all_tests_names = [test.name for test in items]
    for fixer in all_fixers:
        expected_test_name = "test_{}".format(fixer["fixer_callable"].__name__)
        if expected_test_name not in all_tests_names:
            error_message = "No test written for {} fixer '{}'".format(
                fixer["fixer_family"].title(), fixer["fixer_callable"].__name__
            )

            def missing_fixer_test():
                raise RuntimeError(error_message)

            if _fail_fast:  # For testing only
                missing_fixer_test()
            mock_item = copy.copy(
                items[0]
            )  # We expect at least 1 test in the test suite, else it breaks...
            mock_item.parent.name = "test_{}_fixers.py".format(fixer["fixer_family"])
            setattr(
                mock_item.parent.obj,
                "MISSING_" + expected_test_name,
                missing_fixer_test,
            )
            items.append(
                Function(
                    name="MISSING_" + expected_test_name,
                    parent=mock_item.parent,
                    config=config,
                    session=mock_item.session,
                )
            )
