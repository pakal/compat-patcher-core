from __future__ import absolute_import, print_function, unicode_literals

import sys

import pytest

from compat_patcher_core.utilities import (
    PatchingUtilities,
    detuplify_software_version,
    tuplify_software_version,
    WarningsProxy,
)

example_settings = {
    "logging_level": "INFO",
    "enable_warnings": True,
    "patch_injected_objects": True,
}

default_patch_marker = "__COMPAT_PATCHED__"


def test_patch_injected_object():

    patching_utilities = PatchingUtilities(example_settings)

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

    patching_utilities.inject_module("csv.mymodule", dummy_module)
    import csv.mymodule  # Submodules are OK too

    patching_utilities.inject_module("noparent.mymodule", dummy_module)
    with pytest.raises(ImportError, match="No module named"):
        import noparent.module  # Parent module "noparent" must exist first

    assert getattr(new_dummy_module, default_patch_marker) == True

    def mycallable(added):
        return 42 + added

    source_object = MyTemplateResponse()
    source_object.my_attr = mycallable
    target_object = MyTemplateResponse()
    patching_utilities.inject_callable_alias(
        target_object,
        "other_attr",
        source_object=source_object,
        source_attrname="my_attr",
    )
    assert getattr(target_object.other_attr, default_patch_marker) == True
    assert target_object.other_attr(added=2) == 44

    patching_utilities.inject_import_alias("newcsv", real_name="csv")
    from newcsv import DictReader

    del DictReader
    import newcsv

    assert newcsv.__name__ == "csv"


def test_must_exist_parameter():

    patching_utilities = PatchingUtilities(example_settings)

    class Target(object):
        pass

    class MyClass(object):
        pass

    def my_callable():
        return 42

    source_object = Target()
    source_object.source_callable = my_callable

    injectors = [
        (patching_utilities.inject_attribute, dict(attribute=MyClass())),
        (patching_utilities.inject_callable, dict(patch_callable=my_callable)),
        (patching_utilities.inject_class, dict(klass=MyClass)),
        (
            patching_utilities.inject_callable_alias,
            dict(source_object=source_object, source_attrname="source_callable"),
        ),
    ]

    for injector, extra_kwargs in injectors:

        target = Target()

        with pytest.raises(RuntimeError, match="must_exist=True"):
            injector(target, "my_name", must_exist=True, **extra_kwargs)
        assert not hasattr(target, "my_name")  # Untouched

        injector(target, "my_name", must_exist=False, **extra_kwargs)
        assert hasattr(target, "my_name")

        target.my_name = "ORIGINAL"
        with pytest.raises(RuntimeError, match="must_exist=False"):
            injector(target, "my_name", must_exist=False, **extra_kwargs)
        assert target.my_name == "ORIGINAL"  # Untouched

        injector(target, "my_name", must_exist=True, **extra_kwargs)
        assert target.my_name != "ORIGINAL"

        injector(target, "my_name", **extra_kwargs)  # must_exist=None
        injector(target, "my_other_name", must_exist=None, **extra_kwargs)
        assert hasattr(target, "my_other_name")

    import dummy_module

    with pytest.raises(RuntimeError, match="already exists in sys.modules"):
        patching_utilities.inject_module("csv", dummy_module)

    with pytest.raises(RuntimeError, match="must_exist=False"):
        patching_utilities.inject_import_alias("json", real_name="csv", must_exist=False)

    with pytest.raises(RuntimeError, match="must_exist=True"):
        patching_utilities.inject_import_alias(
            "newjson", real_name="json", must_exist=True
        )

    patching_utilities.inject_import_alias(
        "newjson", real_name="json", must_exist=False
    )
    with pytest.raises(RuntimeError, match="must_exist=False"):
        patching_utilities.inject_import_alias(
            "newjson", real_name="json", must_exist=False
        )
    patching_utilities.inject_import_alias(
        "newjson", real_name="json", must_exist=True
    )
    patching_utilities.inject_import_alias("newjson", real_name="json")  # No-op


def test_inject_import_alias_does_not_import_parent_by_default(tmp_path, monkeypatch):

    patching_utilities = PatchingUtilities(example_settings)

    package_dir = tmp_path / "unimportable_package"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        "raise AttributeError('must not be imported')"
    )
    monkeypatch.setattr(sys, "path", [str(tmp_path)] + sys.path)

    patching_utilities.inject_import_alias(
        "unimportable_package.my_alias", real_name="csv"
    )
    assert "unimportable_package" not in sys.modules


def test_patch_injected_objects_setting():

    patching_utilities = PatchingUtilities(example_settings)

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
    from compat_patcher_core.utilities import stdlib_warnings

    patching_utilities = PatchingUtilities(example_settings)

    warnings_proxy = WarningsProxy()  # For now, goes direct lyto stdlib

    stdlib_warnings.simplefilter("always", Warning)

    with stdlib_warnings.catch_warnings(record=True) as w:
        patching_utilities.emit_warning("this feature is obsolete!", DeprecationWarning)
    assert len(w) == 1
    warning = w[0]
    assert "this feature is obsolete!" in str(warning.message)

    with stdlib_warnings.catch_warnings(record=True) as w:
        warnings_proxy.warn("this feature is obsolete too!", DeprecationWarning)
    assert len(w) == 1
    warning = w[0]
    assert "this feature is obsolete too!" in str(warning.message)

    warnings_proxy.set_patching_utilities(patching_utilities)
    with stdlib_warnings.catch_warnings(record=True) as w:
        warnings_proxy.warn("this feature is obsolete again!", DeprecationWarning)
    assert len(w) == 1
    warning = w[0]
    assert "this feature is obsolete again!" in str(warning.message)

    patching_utilities.apply_settings(dict(enable_warnings=False))

    with stdlib_warnings.catch_warnings(record=True) as w:
        patching_utilities.emit_warning("this feature is dead!", DeprecationWarning)
    assert len(w) == 0  # well disabled

    with stdlib_warnings.catch_warnings(record=True) as w:
        warnings_proxy.warn("this feature is obsolete again!", DeprecationWarning)
    assert len(w) == 0  # well disabled


def test_logging_level_setting(capsys):

    patching_utilities = PatchingUtilities(example_settings)

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


def test_module_is_loaded_or_importable():
    assert PatchingUtilities._module_is_loaded_or_importable("sys") is True
    assert PatchingUtilities._module_is_loaded_or_importable("csv") is True
    assert (
        PatchingUtilities._module_is_loaded_or_importable(
            "nonexistent_parent_pkg_xyz.foo"
        )
        is False
    )


def test_version_tuplify_detuplify():
    assert tuplify_software_version((5, 0)) == (5, 0)
    assert tuplify_software_version("5.0") == (5, 0)
    assert tuplify_software_version(None) is None
    assert detuplify_software_version((5, 0)) == "5.0"
    assert detuplify_software_version("5.0") == "5.0"
    assert detuplify_software_version(None) is None
