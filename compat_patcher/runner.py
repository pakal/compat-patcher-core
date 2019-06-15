from __future__ import absolute_import, print_function, unicode_literals

import functools

import six

from compat_patcher.exceptions import SkipFixerException


class PatchingRunner(object):

    _all_applied_fixers = []  # Class attribute with qualified fixer names!

    def __init__(self, config_provider, patching_utilities, patching_registry):
        self._config_provider = config_provider
        self._patching_utilities = patching_utilities
        self._patching_registry = patching_registry

    def _get_patcher_setting(self, name):
        """
        Returns the value of a patcher setting, without necessarily validating it.

        If the `settings` parameters is not None, it has precedence over default settings.
        """
        return self._config_provider[name]

    def get_patcher_setting(self, name):
        """
        Returns the value of a patcher setting, and potentially apply a rough validation.
        """
        value = self._get_patcher_setting(name)

        # For now, patching utilities validate their own settings, so we just check filters
        if name.startswith("include") or name.startswith("exclude"):
            assert value in ("*", None) or (
                isinstance(value, (list, tuple))
                and all(isinstance(f, six.string_types) for f in value)
            ), value

        return value

    def _apply_selected_fixers(self, fixers):
        just_applied_fixers = []
        for fixer in fixers:

            fixer_qualified_name = "%s.%s" % (fixer["fixer_family"], fixer["fixer_id"])

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
        fixer_settings = dict(
            include_fixer_ids=self.get_patcher_setting("include_fixer_ids"),
            include_fixer_families=self.get_patcher_setting("include_fixer_families"),
            exclude_fixer_ids=self.get_patcher_setting("exclude_fixer_ids"),
            exclude_fixer_families=self.get_patcher_setting("exclude_fixer_families"),
        )
        log = functools.partial(self._patching_utilities.emit_log, level="DEBUG")
        relevant_fixers = self._patching_registry.get_relevant_fixers(
            log=log, **fixer_settings
        )

        # REVERSED order is necessary for backwards compatibility, more advanced sorting might be introduced to help
        # forward-compatibility fixers...
        relevant_fixers.sort(
            key=lambda x: (x["fixer_reference_version"], x["fixer_id"]), reverse=True
        )

        return relevant_fixers

    def patch_software(self):
        """Patches the software with relevant fixers, applied in a proper order.

        Returns the list of fixers that were successfully applied during this call.
        """
        # print("Fixers are:", registry.patching_registry)
        relevant_fixers = self._get_sorted_relevant_fixers()
        just_applied_fixers = self._apply_selected_fixers(relevant_fixers)
        return just_applied_fixers
