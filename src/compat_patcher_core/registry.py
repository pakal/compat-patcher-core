from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

import six

from compat_patcher_core.utilities import (
    tuplify_software_version,
    _import_attribute_from_dotted_string,
)


class PatchingRegistry(object):
    """
    This registry is used to store and select a set of fixers related to some
    specific software.

    `family_prefix` will be used to constructe family names, along with the software
    reference version provided by the fixer.

    `populate_callable`, if provided, is a callable taking the registry as first
    argument, and which will be called by `populate()`.

    `current_software_version` may be a version tuple or a string. If it's None,
    then an override value will have to be provided when calling `get_relevant_fixers`.
    """

    def __init__(
        self, family_prefix, populate_callable=None, current_software_version=None
    ):
        assert family_prefix and isinstance(
            family_prefix, six.string_types
        ), family_prefix
        assert populate_callable is None or hasattr(
            populate_callable, "__call__"
        ), populate_callable
        self._family_prefix = family_prefix
        self._is_populated = False
        self._populate_callable = populate_callable
        self._patching_registry = collections.OrderedDict()
        self._current_software_version = current_software_version

    def _get_current_software_version(self):
        """
        Returns a tuple of integers, or a dotted string, representing the current
        version of the software to be patched.
        """
        current_software_version = self._current_software_version
        if six.callable(current_software_version):
            current_software_version = current_software_version()
        assert current_software_version is None or isinstance(
            current_software_version, (six.string_types, tuple, list)
        ), current_software_version
        return current_software_version

    def populate(self):
        """
        Trigger the registration of potential lazy fixers, which might be in other
        submodules, or waiting in factory functions.
        """
        res = None
        if not self._is_populated:
            if self._populate_callable:
                res = self._populate_callable(self)
            self._is_populated = True
        return res

    @staticmethod
    def _extract_docstring(func):
        """Extract and check the docstring of a callable"""
        doc = func.__doc__
        if not doc:
            raise ValueError("Fixer %r must provide a help string" % func)
        return doc

    def register_compatibility_fixer(
        self,
        fixer_reference_version,
        fixer_applied_from_version=None,  # INCLUDING this version
        fixer_applied_upto_version=None,  # EXCLUDING this version
        feature_supported_from_version=None,
        feature_supported_upto_version=None,
        fixer_tags=None,
    ):
        """
        Register a compatibility fixer, which will be activated only if current
        software version is >= `fixer_applied_from_version` and <
        `fixer_applied_upto_version` (let them be None to have no limit).

        The "fixer_reference_version" parameters identifies the software version
        where the breaking change was introduced (for backwards compatibility
        fixers), or where the new feature was introduced (for forwards compatibility
        fixers). It is not related to the appearance of corresponding
        DeprecationWarnings in the software. It is also used to sort fixers when
        applying them, and to generate the name of the family of fixers concerned.

        `feature_supported_from_version` (included) and
        `feature_supported_upto_version` (excluded) may be used to limit the range of
        software versions for which related unit-tests are expected to work (i.e
        versions for which the feature is available, either as a monkey-paching or as
        standard code).

        Version identifiers must be dotted strings, eg. "1.9.1". None means "no limit"
        here.

        `fixer_tags` is a **list** of strings, which can be used to differentiate fixers
        which will be applied at different moments of software startup.
        """

        assert (
            isinstance(fixer_reference_version, six.string_types)
            and fixer_reference_version
        ), fixer_reference_version  # eg. "1.9"
        assert fixer_tags is None or isinstance(fixer_tags, list), fixer_tags

        fixer_family = self._family_prefix + fixer_reference_version
        fixer_reference_version = tuplify_software_version(fixer_reference_version)
        fixer_applied_from_version = tuplify_software_version(
            fixer_applied_from_version
        )
        fixer_applied_upto_version = tuplify_software_version(
            fixer_applied_upto_version
        )
        feature_supported_from_version = tuplify_software_version(
            feature_supported_from_version
        )
        feature_supported_upto_version = tuplify_software_version(
            feature_supported_upto_version
        )
        fixer_tags = fixer_tags or []

        if fixer_applied_from_version and fixer_applied_upto_version:
            assert fixer_applied_from_version < fixer_applied_upto_version
        if feature_supported_from_version and feature_supported_upto_version:
            assert feature_supported_from_version < feature_supported_upto_version

        def _register_simple_fixer(func):
            fixer_id = func.__name__  # untouched ATM, not fully qualified
            new_fixer = dict(
                fixer_callable=func,
                fixer_id=fixer_id,
                fixer_explanation=self._extract_docstring(func),
                fixer_reference_version=fixer_reference_version,
                fixer_family=fixer_family,
                fixer_tags=fixer_tags,
                fixer_applied_from_version=fixer_applied_from_version,
                fixer_applied_upto_version=fixer_applied_upto_version,
                feature_supported_from_version=feature_supported_from_version,
                feature_supported_upto_version=feature_supported_upto_version,
                fixer_qualified_name="%s|%s" % (fixer_family, fixer_id),
            )

            assert fixer_id not in self._patching_registry, (
                "duplicate fixer id %s detected" % fixer_id
            )
            self._patching_registry[fixer_id] = new_fixer
            # print("patching_registry", patching_registry)
            return func

        return _register_simple_fixer

    def get_all_fixers(self):
        """Return the list of all fixers (as dicts) known by this registry."""
        return list(self._patching_registry.values())

    def get_fixer_by_id(self, fixer_id):
        """Return the fixer having this (unqualified) ID, or raise KeyError."""
        return self._patching_registry[fixer_id]

    def get_relevant_fixers(
        self,
        include_fixer_ids="*",
        include_fixer_families=None,
        exclude_fixer_ids=None,
        exclude_fixer_families=None,
        current_software_version=None,
        log=None,
    ):
        """
        Return the list of fixers (as dicts) to be applied for the target software
        version, based on the metadata of fixers, as well as inclusion/exclusion
        lists provided as arguments.

        For inclusion/exclusion filters, a special "*" value means "all fixers",
        else a list of strings is expected.

        An output callable `log` may be provided, expecting a string as argument,
        to debug the reasons why some fixers weren't selected.

        This method forces a populate() on the registry.
        """

        if not current_software_version:
            current_software_version = self._get_current_software_version()
        if not current_software_version:
            raise ValueError(
                "PatchingRegistry must be provided a valid current_software_version "
                "in its constructor or as `get_relevant_fixers` argument."
            )

        self.populate()

        ALL = "*"

        log = log or (lambda x: x)

        current_software_version = tuplify_software_version(current_software_version)

        relevant_fixers = []

        # Shortcut for the common case "no specific inclusion/exclusion lists"
        mass_include = (
            include_fixer_ids == ALL or include_fixer_families == ALL
        ) and not any((exclude_fixer_ids, exclude_fixer_families))

        for fixer_id, fixer in self._patching_registry.items():
            assert fixer_id == fixer["fixer_id"], fixer
            fixer_qualified_name = fixer["fixer_qualified_name"]

            if (
                fixer["fixer_applied_from_version"] is not None
                and current_software_version < fixer["fixer_applied_from_version"]
            ):  # STRICTLY SMALLER
                log(
                    "Skipping fixer %s, useful only in next software versions"
                    % fixer_id
                )
                continue

            if (
                fixer["fixer_applied_upto_version"] is not None
                and current_software_version >= fixer["fixer_applied_upto_version"]
            ):  # GREATER OR EQUAL
                log(
                    "Skipping fixer %s, useful only in previous software versions"
                    % fixer_id
                )
                continue

            if not mass_include:

                included = False
                if include_fixer_ids == ALL or (
                    include_fixer_ids
                    and (
                        fixer_id in include_fixer_ids
                        or fixer_qualified_name in include_fixer_ids
                    )
                ):
                    included = True
                if include_fixer_families == ALL or (
                    include_fixer_families
                    and fixer["fixer_family"] in include_fixer_families
                ):
                    included = True

                if not included:
                    log(
                        "Skipping fixer %s, having neither id nor family (%s) included by patcher settings"
                        % (fixer_id, fixer["fixer_family"])
                    )
                    continue

                if exclude_fixer_ids == ALL or (
                    exclude_fixer_ids
                    and (
                        fixer_id in exclude_fixer_ids
                        or fixer_qualified_name in exclude_fixer_ids
                    )
                ):
                    log("Skipping fixer %s, excluded by patcher settings" % fixer_id)
                    continue

                if exclude_fixer_families == ALL or (
                    exclude_fixer_families
                    and fixer["fixer_family"] in exclude_fixer_families
                ):
                    log(
                        "Skipping fixer %s, having family %s excluded by patcher settings"
                        % (fixer_id, fixer["fixer_family"])
                    )
                    continue

            # cheers, this fixer has passed all filters!
            relevant_fixers.append(fixer)

        return relevant_fixers

    def get_relevant_fixer_ids(self, qualified=False, **kwargs):
        """"Same as `get_relevant_fixers`, but only returns IDs of selected fixers.

        If `qualified` is True, returns a fixers IDs dot-prefixed with the family name."""
        fixers = self.get_relevant_fixers(**kwargs)
        field_name = "fixer_qualified_name" if qualified else "fixer_id"
        return [f[field_name] for f in fixers]


class MultiPatchingRegistry(object):
    """
    This patching registry wraps a list of other registries, each having its own
    fixers and current software version.

    It concatenates and returns selected fixers on demand, assuming that they are
    compatible with each other.
    """

    def __init__(self, registries):
        self._registry_references = registries
        self._is_populated = False
        self._registries = self._load_registries(registries)

    def populate(self):
        res = []
        if not self._is_populated:
            for registry in self._registries:
                res.append(registry.populate())
            self._is_populated = True
        return res

    @staticmethod
    def _load_registries(registry_references):
        registries = []
        for registry_reference in registry_references:

            original_registry_reference = registry_reference

            if isinstance(registry_reference, six.string_types):
                registry_reference = _import_attribute_from_dotted_string(
                    registry_reference
                )

            if six.callable(registry_reference):
                registry_reference = registry_reference()

            if not isinstance(registry_reference, PatchingRegistry):
                raise ValueError(
                    "Wrong registry reference %r" % original_registry_reference
                )

            registries.append(registry_reference)
        assert len(registries) == len(registry_references)
        return registries

    @staticmethod
    def _flatten(list_of_lists):
        return list(itertools.chain(*list_of_lists))

    def get_relevant_fixers(self, *args, **kwargs):
        """Populate underlying registries, and return the concatenation of their
        selected fixers.

        Forcing a `current_software_version` as parameter of this method is still
        possible, but beware that underlying registries all deal with the same
        software stack, in this case.
        """

        self.populate()

        return self._flatten(
            registry.get_relevant_fixers(*args, **kwargs)
            for registry in self._registries
        )

    def get_all_fixers(self, *args, **kwargs):
        """Return the concatenation of all fixers of underlying registries."""
        return self._flatten(
            [registry.get_all_fixers(*args, **kwargs) for registry in self._registries]
        )

    def get_fixer_by_id(self, fixer_id, *args, **kwargs):
        """
        In case of duplicate fixers having the same ID, just return the first one.
        """
        for registry in self._registries:
            try:
                return registry.get_fixer_by_id(fixer_id, *args, **kwargs)
            except KeyError:
                pass
        raise KeyError("Fixer %r not found in any patching registries" % fixer_id)

    get_relevant_fixer_ids = six.get_unbound_function(
        PatchingRegistry.get_relevant_fixer_ids
    )  # Unmodified
