from __future__ import absolute_import, print_function, unicode_literals

import os
import warnings

import pytest

import compat_patcher
from compat_patcher.registry import PatchingRegistry
from compat_patcher.utilities import (
    PatchingUtilities,
    ensure_no_stdlib_warnings,
    detuplify_software_version,
    tuplify_software_version,
    WarningsProxy,
    ensure_all_fixers_have_a_test_under_pytest,
)

example_config_provider = {
    "logging_level": "INFO",
    "enable_warnings": True,
    "patch_injected_objects": True,
}

default_patch_marker = "__COMPAT_PATCHED__"


def test_patch_injected_object():

    patching_utilities = PatchingUtilities(example_config_provider)

    import dummy_module

    class MyTemplateResponse:
        pass

    patching_utilities.inject_class(
        dummy_module, "MyTemplateResponse", MyTemplateResponse
    )
    assert getattr(dummy_module.MyTemplateResponse, default_patch_marker) == True
    del dummy_module.MyTemplateResponse

    response = MyTemplateResponse()

    patching_utilities.inject_attribute(dummy_module, "_response_", response)
    assert getattr(dummy_module._response_, default_patch_marker) == True
    del dummy_module._response_

    def delete_selected():
        pass

    patching_utilities.inject_callable(dummy_module, "delete_selected", delete_selected)
    assert getattr(dummy_module.delete_selected, default_patch_marker) == True

    patching_utilities.inject_module("new_dummy_module", dummy_module)
    import new_dummy_module

    assert getattr(new_dummy_module, default_patch_marker) == True

    def mycallable(added):
        return 42 + added

    source_object = MyTemplateResponse()
    source_object.my_attr = mycallable
    target_object = MyTemplateResponse()
    patching_utilities.inject_callable_alias(
        source_object, "my_attr", target_object, "other_attr"
    )
    assert getattr(target_object.other_attr, default_patch_marker) == True
    assert target_object.other_attr(added=2) == 44

    patching_utilities.inject_import_alias("newcsv", real_name="csv")
    from newcsv import DictReader

    del DictReader
    import newcsv

    assert newcsv.__name__ == "csv"


def test_patch_injected_objects_setting():

    patching_utilities = PatchingUtilities(example_config_provider)

    import dummy_module

    class MyMock(object):
        def method(self):
            return True

    my_mock = MyMock()
    my_mock2 = MyMock()

    patching_utilities.apply_settings(dict(patch_injected_objects="myattrname"))
    patching_utilities.inject_attribute(dummy_module, "new_stuff", my_mock)
    assert dummy_module.new_stuff.myattrname is True
    patching_utilities.inject_attribute(dummy_module, "new_stuff2", my_mock.method)
    assert not hasattr(
        dummy_module.new_stuff2, "myattrname"
    )  # Bound method has no __dict__

    patching_utilities.apply_settings(dict(patch_injected_objects=False))
    patching_utilities.inject_attribute(dummy_module, "other_stuff", my_mock2)
    assert not dummy_module.other_stuff.__dict__  # No extra marker


def test_enable_warnings_setting():

    patching_utilities = PatchingUtilities(example_config_provider)

    warnings_proxy = WarningsProxy()  # For now, goes direct lyto stdlib

    warnings.simplefilter("always", Warning)

    with warnings.catch_warnings(record=True) as w:
        patching_utilities.emit_warning("this feature is obsolete!", DeprecationWarning)
    assert len(w) == 1
    warning = w[0]
    assert "this feature is obsolete!" in str(warning.message)

    with warnings.catch_warnings(record=True) as w:
        warnings_proxy.warn("this feature is obsolete too!", DeprecationWarning)
    assert len(w) == 1
    warning = w[0]
    assert "this feature is obsolete too!" in str(warning.message)

    warnings_proxy.set_patching_utilities(patching_utilities)
    with warnings.catch_warnings(record=True) as w:
        warnings_proxy.warn("this feature is obsolete again!", DeprecationWarning)
    assert len(w) == 1
    warning = w[0]
    assert "this feature is obsolete again!" in str(warning.message)

    patching_utilities.apply_settings(dict(enable_warnings=False))

    with warnings.catch_warnings(record=True) as w:
        patching_utilities.emit_warning("this feature is dead!", DeprecationWarning)
    assert len(w) == 0  # well disabled

    with warnings.catch_warnings(record=True) as w:
        warnings_proxy.warn("this feature is obsolete again!", DeprecationWarning)
    assert len(w) == 0  # well disabled


def test_logging_level_setting(capsys):

    patching_utilities = PatchingUtilities(example_config_provider)

    patching_utilities.emit_log("<DEBUGGING1>", "DEBUG")
    patching_utilities.emit_log("<INFORMATION1>")  # default value

    out, err = capsys.readouterr()
    assert "<DEBUGGING1>" not in err
    assert "<INFORMATION1>" in err

    patching_utilities.apply_settings(dict(logging_level=None))

    patching_utilities.emit_log("<DEBUGGING2>", "DEBUG")
    patching_utilities.emit_log("<INFORMATION2>", "INFO")

    out, err = capsys.readouterr()
    assert "<DEBUGGING2>" not in err
    assert "<INFORMATION2>" not in err

    patching_utilities.apply_settings(dict(logging_level="DEBUG"))

    patching_utilities.emit_log("<DEBUGGING3>", "DEBUG")
    patching_utilities.emit_log("<INFORMATION3>", "INFO")

    out, err = capsys.readouterr()
    assert "<DEBUGGING3>" in err
    assert "<INFORMATION3>" in err


def test_no_stdlib_warnings_in_package():
    import warnings  # This line will trigger checker error

    del warnings
    pkg_root = os.path.dirname(compat_patcher.__file__)
    analysed_files = ensure_no_stdlib_warnings(pkg_root)
    assert len(analysed_files) > 5, analysed_files

    pkg_root = os.path.dirname(__file__)
    with pytest.raises(ValueError, match="wrong phrase.*test_patching_utilities.py"):
        ensure_no_stdlib_warnings(pkg_root)


def test_version_tuplify_detuplify():
    assert tuplify_software_version((5, 0)) == (5, 0)
    assert tuplify_software_version("5.0") == (5, 0)
    assert tuplify_software_version(None) is None
    assert detuplify_software_version((5, 0)) == "5.0"
    assert detuplify_software_version("5.0") == "5.0"
    assert detuplify_software_version(None) is None


def test_ensure_all_fixers_have_a_test_under_pytest():
    class DummyNode:
        pass

    patching_registry = PatchingRegistry("dummyname")

    @patching_registry.register_compatibility_fixer(fixer_reference_version="10.1")
    def my_dummy_fixer(utils):
        "A help string"
        pass

    node = DummyNode()
    node.name = "test_my_dummy_fixer"
    items = [node]

    # No problem, all registered fixers have their test here
    ensure_all_fixers_have_a_test_under_pytest(
        config=None, items=items, patching_registry=patching_registry, _fail_fast=True
    )

    # Error when attempting to clone first item to report the missing test
    with pytest.raises(RuntimeError, match="No test written for .* fixer"):
        ensure_all_fixers_have_a_test_under_pytest(
            config=None, items=[], patching_registry=patching_registry, _fail_fast=True
        )
