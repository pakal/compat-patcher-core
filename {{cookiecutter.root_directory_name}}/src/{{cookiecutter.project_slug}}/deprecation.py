from __future__ import absolute_import, print_function, unicode_literals

from compat_patcher_core.utilities import WarningsProxy

# Proxy meant to be imported on top of copy/pasted legacy code, instead of the stdlib "warnings" package.
# From inside fixers, it's best to use utils.emit_warnings() directly.
warnings = WarningsProxy()

# Here put DeprecationWarning subclasses and other deprecation utilities for your fixers
