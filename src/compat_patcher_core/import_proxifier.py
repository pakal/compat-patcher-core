"""This module allows to create aliases between packages, so that one can import a
module under a different name (mainly for retrocompatibility purpose).

Note that it is NOT about aliasing local references to modules after import, eg. with
"from package import module_name as other_module_name".
Here we really deal with aliasing the "full name" of the module, as it will appear in
sys.modules.

There are different ways of implementing "import aliases":

- overridding __import__ (difficult, since this API loads parent modules too)
- using a custom module loader which creates a wrapper class (with setattr,
  getattr etc...), and injects it as a proxy in sys.modules[alias]
- using a custom module loader, which simply copies a reference to the real module
  into sys.modules (and on recent python version, updates its __spec__ to gives hints
  about this operation).
  *THIS* is the way it is currently implemented, so that imported modules keep being
  SINGLETONS whatever their
  possible aliases.

Beware about not creating loops with your aliases, as this could trigger infinite
recursions.
"""

import contextlib
import importlib
import sys

# Maps ALIASES to REAL MODULES
MODULES_ALIASES_REGISTRY = []


@contextlib.contextmanager
def enrich_import_error(alias_name):
    try:
        yield
    except ImportError as e:
        # ImportError exception has different structure between py2k and py3k
        enrich_message = lambda msg: "%s (when loading alias name '%s')" % (
            msg,
            alias_name,
        )
        if hasattr(e, "msg"):  # py3k
            e.msg = enrich_message(e.msg)
        else:  # py2k, the "message" attribute is actually ignored by __str__
            e.args = (enrich_message(e.args[0]),)
        raise


def register_module_alias(alias_name, real_name):
    assert not alias_name.startswith("."), alias_name
    assert not real_name.startswith("."), real_name
    assert (
        alias_name != real_name
    ), alias_name  # lots of other import cycles are possible though
    entry = (alias_name, real_name)
    if entry not in MODULES_ALIASES_REGISTRY:
        MODULES_ALIASES_REGISTRY.append(entry)
        return True
    return False


def _get_module_alias_real_name(fullname):
    """
    Returns the real name of module (when fullname is an alias name) or None.
    """
    for k, v in MODULES_ALIASES_REGISTRY:
        if (k == fullname) or fullname.startswith(k + "."):
            return fullname.replace(k, v)
    return None


try:

    import importlib.machinery, importlib.abc

except ImportError:

    # OLD STYLE : we use PEP 302 find_module/load_module API, available for python2.7+

    _is_new_style_proxifier = False

    class AliasingLoader(object):
        def __init__(self, real_name, alias_name):
            self.real_name = real_name
            self.alias_name = alias_name

        def load_module(self, name):
            if name in sys.modules:
                return sys.modules[name]  # Shortcut
            # We let the standard machinery handle sys.modules, module attrs etc.
            with enrich_import_error(self.alias_name):
                module = importlib.import_module(self.real_name, package=None)
            sys.modules[name] = module  # cached
            return module

    class ModuleAliasFinder(object):
        @classmethod
        def find_module(self, fullname, *args, **kwargs):
            real_name = _get_module_alias_real_name(fullname)
            if real_name is None:
                return None  # no aliased module is known
            return AliasingLoader(real_name=real_name, alias_name=fullname)


else:

    # NEW STYLE : we use modern import hooks (PEP 451 etc.)

    _is_new_style_proxifier = True

    class AliasingLoader(importlib.abc.Loader):

        target_spec_backup = None

        def __init__(self, real_name, alias_name):
            self.real_name = real_name
            self.alias_name = alias_name

        def create_module(self, spec):
            # We do the real loading of aliased module here
            with enrich_import_error(self.alias_name):
                module = importlib.import_module(self.real_name, package=None)
            # Normally we have module.__name__ == self.real_name here, but it's not reliable
            # e.g. six "_importer" delivers six.moves.urllib.parse module with __name__ six.moves.urllib_parse
            self.target_spec_backup = module.__spec__
            return module

        def exec_module(self, module):
            # __name__ is, on some python versions, overridden as self.alias_name by init_module_attrs(_force_name=True)
            # (in addition to false names set by custom importers, as described above)
            module.__name__ = self.real_name
            assert module.__spec__.origin == "alias", module.__spec__  # well overridden
            assert module.__spec__.loader_state["aliased_spec"] is None
            assert self.target_spec_backup, self.target_spec_backup
            module.__spec__.loader_state["aliased_spec"] = self.target_spec_backup
            pass  # nothing else to do, module already loaded

    class ModuleAliasFinder(importlib.abc.MetaPathFinder):
        """
        Note : due to new call of _init_module_attrs(spec...) on aliased
        module, its __spec__ attribute will be changed by this new import...
        """

        @classmethod
        def find_spec(cls, fullname, *args, **kwargs):

            # print("MetaPathFinder FINDSPEC", fullname, args, kwargs)

            real_name = _get_module_alias_real_name(fullname)
            if real_name is None:
                return None  # no aliased module is known

            # TODO emit warnings/logging

            alias_loader = AliasingLoader(real_name=real_name, alias_name=fullname)

            spec = importlib.machinery.ModuleSpec(
                name=fullname,
                loader=alias_loader,
                origin="alias",
                loader_state={"aliased_name": fullname, "aliased_spec": None},
                is_package=True,
            )  # in doubt, assume...

            return spec


def install_import_proxifier():
    """
    Add a meta path hook before all others, so that new module loadings
    may be redirected to aliased module.

    Idempotent function.
    """
    if ModuleAliasFinder not in sys.meta_path:
        sys.meta_path.insert(0, ModuleAliasFinder)
    assert ModuleAliasFinder in sys.meta_path, sys.meta_path
