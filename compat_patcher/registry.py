from __future__ import absolute_import, print_function, unicode_literals

import collections

from django.utils import six

from compat_patcher.utilities import tuplify_software_version

class PatchingRegistry(object):

    def __init__(self, family_prefix):
        self._family_prefix = family_prefix
        self._patching_registry = collections.OrderedDict()

    @staticmethod
    def _extract_docstring(func):
        """Extract and check the docstring of a callable"""
        doc = func.__doc__
        if not doc:
            raise ValueError("Fixer %r must provide a help string" % func)
        return doc

    def register_compatibility_fixer(self,
                                     fixer_reference_version,
                                     fixer_applied_from_version=None,  # INCLUDING this version
                                     fixer_applied_upto_version=None,  # EXCLUDING this version
                                     feature_supported_from_version=None,
                                     feature_supported_upto_version=None,
                                     fixer_tags=None):
        """
        Registers a compatibility fixer, which will be activated only if current software version
        is >= `fixer_applied_from_version` and < `fixer_applied_upto_version` (let them be None to have no limit).

        `fixer_reference_version` is used to sort fixers when applying them, and to derive the name of the fixers family concerned.

        `feature_supported_from_version` (included) and `feature_supported_upto_version` (excluded) may be used to limit
        the range of software versions for which related unit-tests are expected to work (i.e versions
        for which the feature is available, either as a monkey-paching or as standard code).

        Version identifiers must be dotted strings, eg. "1.9.1".

        `fixer_tags` is a **list** of strings, which can be used to separate fixers which will be applied at different moments of software startup.


        """

        assert isinstance(fixer_reference_version, six.string_types), fixer_reference_version  # eg. "1.9"
        assert fixer_tags is None or isinstance(fixer_tags, list), fixer_tags

        fixer_family = self._family_prefix + fixer_reference_version
        fixer_reference_version=tuplify_software_version(fixer_reference_version)
        fixer_applied_from_version=tuplify_software_version(fixer_applied_from_version)
        fixer_applied_upto_version=tuplify_software_version(fixer_applied_upto_version)
        feature_supported_from_version=tuplify_software_version(feature_supported_from_version)
        feature_supported_upto_version=tuplify_software_version(feature_supported_upto_version)
        fixer_tags = fixer_tags or []

        if fixer_applied_from_version and fixer_applied_upto_version:
            assert fixer_applied_from_version < fixer_applied_upto_version
        if feature_supported_from_version and feature_supported_upto_version:
            assert feature_supported_from_version < feature_supported_upto_version

        def _register_simple_fixer(func):
            fixer_id = func.__name__  # untouched ATM, not fully qualified
            new_fixer = dict(fixer_callable=func,
                             fixer_id=fixer_id,
                             fixer_explanation=self._extract_docstring(func),
                             fixer_reference_version=fixer_reference_version,
                             fixer_family=fixer_family,
                             fixer_tags=fixer_tags,
                             fixer_applied_from_version=fixer_applied_from_version,
                             fixer_applied_upto_version=fixer_applied_upto_version,
                             feature_supported_from_version=feature_supported_from_version,
                             feature_supported_upto_version=feature_supported_upto_version)

            assert fixer_id not in self._patching_registry, "duplicate fixer id %s detected" % fixer_id
            self._patching_registry[fixer_id] = new_fixer
            # print("patching_registry", patching_registry)
            return func

        return _register_simple_fixer


    def get_all_fixers(self):
        return list(self._patching_registry.values())

    def get_fixer_by_id(self, fixer_id):
        return self._patching_registry[fixer_id]


    def get_relevant_fixers(self,
                            current_software_version,
                            include_fixer_ids="*",
                            include_fixer_families=None,
                            exclude_fixer_ids=None,
                            exclude_fixer_families=None,
                            log=None):
        """
        Returns the list of fixers to be applied for the target software version, based on the
        metadata of fixers, as well as inclusion/exclusion lists provided as arguments.

        For inclusion/exclusion filters, a special "*" value means "all fixers", else a list of strings is expected.

        An output callable `log` may be provided, expecting a string as argument.
        """

        ALL = "*"

        log = log or (lambda x:x)

        current_software_version = tuplify_software_version(current_software_version)

        relevant_fixers = []

        # Shortcut for the common case "no specific inclusion/exclusion lists"
        mass_include = ((include_fixer_ids == ALL or include_fixer_families == ALL) and not any((exclude_fixer_ids, exclude_fixer_families)))

        for fixer_id, fixer in self._patching_registry.items():
            assert fixer_id == fixer["fixer_id"], fixer

            if (fixer["fixer_applied_from_version"] is not None and
                    current_software_version < fixer["fixer_applied_from_version"]):  # STRICTLY SMALLER
                log("Skipping fixer %s, useful only in subsequent software versions" % fixer_id)
                continue

            if (fixer["fixer_applied_upto_version"] is not None and
                    current_software_version >= fixer["fixer_applied_upto_version"]):  # GREATER OR EQUAL
                log("Skipping fixer %s, useful only in previous software versions" % fixer_id)
                continue

            if not mass_include:

                included = False
                if include_fixer_ids == ALL or (include_fixer_ids and fixer_id in include_fixer_ids):
                    included = True
                if include_fixer_families == ALL or (include_fixer_families and fixer["fixer_family"] in include_fixer_families):
                    included = True

                if not included:
                    log("Skipping fixer %s, having neither id nor family (%s) included by patcher settings" % (fixer_id, fixer["fixer_family"]))
                    continue

                if exclude_fixer_ids == ALL or (exclude_fixer_ids and fixer_id in exclude_fixer_ids):
                    log("Skipping fixer %s, excluded by patcher settings" % fixer_id)
                    continue

                if exclude_fixer_families == ALL or (exclude_fixer_families and fixer["fixer_family"] in exclude_fixer_families):
                    log("Skipping fixer %s, having family %s excluded by patcher settings" % (fixer_id, fixer["fixer_family"]))
                    continue

            # cheers, this fixer has passed all filters!
            relevant_fixers.append(fixer)

        return relevant_fixers

    def get_relevant_fixer_ids(self, *args, **kwargs):
        fixers = self.get_relevant_fixers(*args, **kwargs)
        return [f["fixer_id"] for f in fixers]

