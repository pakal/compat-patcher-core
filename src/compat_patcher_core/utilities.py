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
    is provided - thus making Warnings controllable by compat patcher settings.
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

    settings_keys_used = ["logging_level", "enable_warnings", "patch_injected_objects"]

    def __init__(self, settings):
        # We force extraction of values, in case settings is a lazy instance
        # and not just a dict
        assert settings, settings
        settings = {name: settings[name] for name in self.settings_keys_used}

        self.apply_settings(settings)

    def apply_settings(self, settings):
        """This method can be called at runtime, mainly to alter the emission of logs
        and Warnings by fixers. it's possible to provide only a subset of settings, the
        others remaining as is.
        """
        if "logging_level" in settings:
            assert settings["logging_level"] is None or hasattr(
                logging, settings["logging_level"]
            ), settings["logging_level"]
            self._logging_level = settings["logging_level"]
        if "enable_warnings" in settings:
            assert settings["enable_warnings"] in (True, False), settings[
                "enable_warnings"
            ]
            self._enable_warnings = settings["enable_warnings"]
        if "patch_injected_objects" in settings:
            patch_injected_objects = settings["patch_injected_objects"]
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
        """Inject a simple callable (not a class) into an object of any type (module, class, instance...).

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

        It is good practice to, then, also inject this module object as an attribute
        of its immediate parents (with inject_attribute()), since this is normally done 
        during python imports.

        :param target_module_name: The dotted name of the new module in sys.modules
        :param module: The module object to inject
        """
        target_module_name = str(target_module_name)  # Python2 compatibility
        assert isinstance(module, types.ModuleType), module
        assert sys.modules.get(target_module_name) is None, target_module_name

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

        from compat_patcher_core import import_proxifier

        import_proxifier.install_import_proxifier()  # idempotent activation
        import_proxifier.register_module_alias(
            alias_name=alias_name, real_name=real_name
        )


def _import_attribute_from_dotted_string(dotted_string):
    """Turns `mymodule.mysubmodule.my_attr` into the imported my_attr
    object, be it a class or an instance.
    """
    module_name, attr_name = dotted_string.rsplit(".", 1)
    module = importlib.import_module(module_name)
    attribute = getattr(module, attr_name)
    return attribute
