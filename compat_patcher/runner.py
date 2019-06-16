from __future__ import absolute_import, print_function, unicode_literals

import functools

import six

from compat_patcher.exceptions import SkipFixerException


class PatchingRunner(object):
    """
    This class is in charge of fetching relevant fixers from the registry,
    and applying them in a proper order, while skipping those who have already been
    applied (i.e same family name and ID) and those which raised SkipFixerException.
    """

    # Helpful for autodocumentation
    config_keys_used = ["include_fixer_ids", "include_fixer_families",
                        "exclude_fixer_ids", "exclude_fixer_families"]

    _all_applied_fixers = []  # Class attribute with qualified fixer names!

    def __init__(self, config_provider, patching_registry, patching_utilities):
        assert config_provider, config_provider
        self._config_provider = config_provider
        self._patching_registry = patching_registry
        self._patching_utilities = patching_utilities

    @classmethod
    def _clear_all_applied_fixers(cls):  # For testing only!
        del cls._all_applied_fixers[:]

    def _get_patcher_setting(self, name):
        """
        Returns the value of a patcher setting.
        """
        assert name in self.config_keys_used  # To track coherence

        value = self._config_provider[name]

        # For now, patching utilities validate their own config, so we just check filters
        if name.startswith("include") or name.startswith("exclude"):
            assert value in ("*", None) or (
                isinstance(value, (list, tuple))
                and all(isinstance(f, six.string_types) for f in value)
            ), value

        return value

    def _apply_selected_fixers(self, fixers):
        just_applied_fixers = []
        for fixer in fixers:

            fixer_qualified_name = fixer["fixer_qualified_name"]

            if fixer_qualified_name not in self._all_applied_fixers:
                self._patching_utilities.emit_log(
                    "Compat fixer '{}-{}' is getting applied".format(
                        fixer["fixer_family"], fixer["fixer_id"]
                    ),
                    level="INFO",
                )
                try:
                    fixer["fixer_callable"](self._patching_utilities)
                    self._all_applied_fixers.append(fixer_qualified_name)
                    just_applied_fixers.append(fixer["fixer_id"])
                except SkipFixerException as e:
                    self._patching_utilities.emit_log(
                        "Compat fixer '{}-{}' was actually not applied, reason: {}".format(
                            fixer["fixer_family"], fixer["fixer_id"], e
                        ),
                        level="WARNING",
                    )
            else:
                self._patching_utilities.emit_log(
                    "Compat fixer '{}' was already applied".format(fixer["fixer_id"]),
                    level="WARNING",
                )
        return just_applied_fixers

    def _get_sorted_relevant_fixers(self):

        # For now, we don't need to be able to force-send a `current_software_version`
        fixers_config = dict(
            include_fixer_ids=self._get_patcher_setting("include_fixer_ids"),
            include_fixer_families=self._get_patcher_setting("include_fixer_families"),
            exclude_fixer_ids=self._get_patcher_setting("exclude_fixer_ids"),
            exclude_fixer_families=self._get_patcher_setting("exclude_fixer_families"),
        )
        log = functools.partial(self._patching_utilities.emit_log, level="DEBUG")
        relevant_fixers = self._patching_registry.get_relevant_fixers(
            log=log, **fixers_config
        )

        # REVERSED order is necessary for backwards compatibility, more advanced
        # sorting might be introduced to help forward-compatibility fixers...
        relevant_fixers.sort(
            key=lambda x: (x["fixer_reference_version"], x["fixer_id"]), reverse=True
        )

        return relevant_fixers

    def patch_software(self):
        """Patch the software according to plans.

        Return the list of fixers that were successfully applied during this call.
        """
        relevant_fixers = self._get_sorted_relevant_fixers()
        just_applied_fixers = self._apply_selected_fixers(relevant_fixers)
        return just_applied_fixers
