from __future__ import absolute_import, print_function, unicode_literals

import functools
import importlib
import logging
import sys
import types
import warnings as stdlib_warnings  # Do NOT import/use elsewhere than here!

import six


def tuplify_software_version(version):
    """
    Coerces the version string (if not None), to a version tuple.
    E.g. "1.7.0" becomes (1, 7, 0). No version suffix like "alpha" is expected.
    """
    if version is None:
        return version
    if isinstance(version, six.string_types):
        version = tuple(int(x) for x in version.split("."))
    assert len(version) <= 5, version
    assert all(isinstance(x, six.integer_types) for x in version), version
    return version


def detuplify_software_version(version):
    """
    Coerces the version tuple (if not None), to a version string.
    E.g. (1, 7, 0) becomes "1.7.0".
    """
    if version is None:
        return version
    if isinstance(version, (tuple, list)):
        version = ".".join(str(number) for number in version)
    assert isinstance(version, six.string_types)
    return version


class WarningsProxy(object):
    """An instance of this class acts as a replacement for the stdlib "warnings"
    package, but it relies on a PatchingUtilities instance as soon as this one
    is provided - thus making Warnings controllable by compat patcher config.
    """

    _patching_utilities = None

    def set_patching_utilities(self, patching_utilities):
        assert isinstance(patching_utilities, PatchingUtilities), patching_utilities
        self._patching_utilities = patching_utilities

    def warn(self, *args, **kwargs):
        if self._patching_utilities:
            self._patching_utilities.emit_warning(*args, **kwargs)
        else:
            # Compat patcher is not yet configured
            stdlib_warnings.warn(*args, **kwargs)


class PatchingUtilities(object):
    """
    An instance of this class is provided as first argument to each compatibility fixer
    applied.

    It provides handy tools to monkey-patch the software environment, and emit logs and
    Warnings in a controllable way.

    For better forward-compatibility, please call injection utilities though keyword
    arguments, and not positional ones (due to python2.7 support, it's not
    enforced yet).
    """

    _logging_level = None
    _enable_warnings = False
    _patch_injected_objects = None

    config_keys_used = ["logging_level", "enable_warnings", "patch_injected_objects"]

    def __init__(self, config_provider):
        # We force extraction of values, in case config_provider is a lazy instance
        # and not just a dict
        assert config_provider, config_provider
        config = {name: config_provider[name] for name in self.config_keys_used}

        self.apply_config(config)

    def apply_config(self, config):
        """This method can be called at runtime, mainly to alter the emission of logs
        and Warnings by fixers. it's possible to provide only a subset of settings, the
        others remaining as is.
        """
        if "logging_level" in config:
            assert config["logging_level"] is None or hasattr(
                logging, config["logging_level"]
            ), config["logging_level"]
            self._logging_level = config["logging_level"]
        if "enable_warnings" in config:
            assert config["enable_warnings"] in (True, False), config["enable_warnings"]
            self._enable_warnings = config["enable_warnings"]
        if "patch_injected_objects" in config:
            patch_injected_objects = config["patch_injected_objects"]
            if patch_injected_objects is True:
                patch_injected_objects = "__COMPAT_PATCHED__"  # Default marker name
            assert not patch_injected_objects or isinstance(
                patch_injected_objects, six.string_types
            ), repr(patch_injected_objects)
            self._patch_injected_objects = patch_injected_objects

    @staticmethod
    def _is_simple_callable(obj):
        return isinstance(
            obj, (types.FunctionType, types.BuiltinFunctionType, functools.partial)
        )

    def _patch_injected_object(self, object_to_patch):
        """Mark shim object with a custom boolean attribute, to help identify it via
        introspection.

        Returns a boolean indicating whether the marking worked (some objects don't
        have a writable __dict__).
        """
        assert object_to_patch not in (True, False, None), object_to_patch
        if self._patch_injected_objects:
            try:
                setattr(object_to_patch, self._patch_injected_objects, True)
                return True
            except AttributeError:
                return False  # properties, bound methods and such can't be modified
        return None

    def emit_log(self, message, level="INFO"):
        """A logger printing to stderr, since at some stages of patching, logging is
        not yet setup.

        Log is only output if `level` is gerater or equal the current `logging_level`
        setting.
        """
        min_logging_level = self._logging_level
        if min_logging_level is None:
            return  # No logging at all
        if getattr(logging, level) < getattr(logging, min_logging_level):
            return
        full_message = "[DCP_%s] %s" % (level, message)
        print(full_message, file=sys.stderr)

    def emit_warning(self, message, category=DeprecationWarning, stacklevel=1):
        """Similar to "warnings.warn()" of the stdlib, but only emits the Warning if
        `enable_warnings` setting is True.
        """
        if self._enable_warnings:
            stdlib_warnings.warn(message, category, stacklevel + 1)

    def inject_attribute(self, target_object, target_attrname, attribute):
        """Inject an attribute into an object of any type (module, class, instance...).

        :param target_object: The object to patch
        :param target_attrname: The name given to the new attribute in the object to patch
        :param attribute: The attribute to inject, which must not be a callable
        """
        assert attribute is not None
        assert not self._is_simple_callable(attribute), attribute
        assert not isinstance(attribute, six.class_types), attribute

        self._patch_injected_object(attribute)
        setattr(target_object, target_attrname, attribute)

    def inject_callable(self, target_object, target_callable_name, patch_callable):
        """Inject a callable into an object of any type (module, class, instance...).

        :param target_object: The object to patch
        :param target_callable_name: The name given to the new callable in the object to patch
        :param patch_callable: The callable to inject, which must be a callable, but not a class
        """
        assert self._is_simple_callable(patch_callable), patch_callable

        self._patch_injected_object(patch_callable)
        setattr(target_object, target_callable_name, patch_callable)

    def inject_callable_alias(
        self, target_object, target_attrname, source_object, source_attrname
    ):
        """
        Create and inject an alias for the source callable (not a class), which also
        triggers a deprecation warning when called.

        Returns the created alias callable.

        :param target_object: The object to patch
        :param target_attrname: The name of the callable on the target object
        :param source_object: The object from which to get the callable
        :param source_attrname: The name of the callable on the source object
        """
        source_callable = getattr(source_object, source_attrname)
        assert self._is_simple_callable(source_callable), source_callable

        @functools.wraps(source_callable)
        def wrapper(*args, **kwds):
            # we dunno if it's a backwards or forwards compatibility shim...
            self.emit_warning(
                "%s.%s, which is an alias for %s.%s, was called. One of these is deprecated."
                % (target_object, source_attrname, source_object, source_attrname),
                category=DeprecationWarning,
            )
            return source_callable(*args, **kwds)

        self._patch_injected_object(wrapper)
        setattr(target_object, target_attrname, wrapper)

        return wrapper

    def inject_class(self, target_object, target_klassname, klass):
        """Inject a class into an object of any type (module, class, instance...).

        :param target_object: The object to patch
        :param target_klassname: The name given to the new class in the object to patch
        :param klass: The class to inject
        """
        assert isinstance(klass, six.class_types), klass

        self._patch_injected_object(klass)
        setattr(target_object, target_klassname, klass)

    def inject_module(self, target_module_name, module):
        """Inject a module in sys.modules, under the selected dotted name.

        When injecting a submodule, its parent module(s) must exist too.

        :param target_module_name: The dotted name of the new module in sys.modules
        :param module: The module object to inject
        """
        target_module_name = str(target_module_name)  # Python2 compatibility
        assert isinstance(module, types.ModuleType), module
        assert sys.modules.get(target_module_name) is None

        self._patch_injected_object(module)

        sys.modules[target_module_name] = module

    def inject_import_alias(self, alias_name, real_name):
        """Create an import alias for the selected module.

        This doesn't directly patch sys.modules, but instead uses the imports hooks
        of python, so that "import <alias_name>" and "import <real_name>" both end up
        importing the same the (sub)module object.

        When the alias is a submodule, its parent module(s) must exist too.

        :param alias_name: The dotted name of the alias module
        :param real_name: The dotted name of the real module
        """

        from compat_patcher import import_proxifier

        import_proxifier.install_import_proxifier()  # idempotent activation
        import_proxifier.register_module_alias(
            alias_name=alias_name, real_name=real_name
        )


def ensure_no_stdlib_warnings(
    source_root,
    # we authorize "warnings.warn", as long as it uses the custom WarningsProxy above
    forbidden_phrases=("import warnings", "from warnings"),
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
                        "import warnings as stdlib_warnings" in data
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
            from compat_patcher.utilities import ensure_all_fixers_have_a_test_under_pytest
            ensure_all_fixers_have_a_test_under_pytest(
                    config=config, items=items, patching_registry=django_patching_registry)
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


def _import_attribute_from_dotted_string(dotted_string):
    """Turns `mymodule.mysubmodule.my_attr` into the imported my_attr
    object, be it a class or an instance.
    """
    module_name, attr_name = dotted_string.rsplit(".", 1)
    module = importlib.import_module(module_name)
    attribute = getattr(module, attr_name)
    return attribute