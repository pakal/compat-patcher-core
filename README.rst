.. image:: https://travis-ci.com/pakal/compat-patcher-core.svg?branch=master
    :target: https://travis-ci.com/pakal/compat-patcher-core


*Long term API compatibility for fast-moving projects*


Welcome to **Compat Patcher Core**, a mini-framework to build **Compatibility Patchers**. These companion applications
allow your favorite software (a framework, a library...) to keep long term API stability towards its ecosystem
(plugins, bridges to other applications...), while still keeping the main codebase clean, and getting new features at
a good pace.

Compatibility Patchers inject backward/forward compatibility shims (like class/function/attribute aliases), restore
features which were dropped/externalized because "not used enough" or "outside the scope of the library", and tweak
the signatures and behaviour of callables (eg. for arguments which disappeared, or which became mandatory). It can
even setup lazy "import aliases", so that code can import a moved module both from its old and new location.

These shims allows you to upgrade your dependencies one at a time, when their maintainer finally had some time for a
code update, or when missing features and bugfixes justify a fork. Most importantly, they allow you to not get stuck,
when deadlines are tight, and crucial dependencies have conflicting expectations regarding the software version.

Note that compatibility Patchers are not supposed to undo changes related to security (default access permissions,
markup escaping, cookie parameters...), because of the risks involved. Also, changes that only impact project-level
code (eg. new mandatory *settings*) should not get patched, since it's easier and cleaner for to simply update project
code.

Technically, Compatibility Patchers are packages which manage a set of **fixers**, tiny utilities (often less than 10
lines of code) which advertise the change that they make, the software versions that they support, and which patch the
target code on demand. By applying these fixers in a proper order (sometimes before, sometimes after the
initialization of the patched software itself), Compatibility Patchers can easily "time travel", and work around multiple
breaking changes which target the same part of the code (e.g. a content handler being added and then removed).

Compat Patcher Core holds the core logice of that system, via easily extendable classes: a registry system,
monkey-patching utilities, and a generic runner to be called at the very start of your application. It also contains
a **cookiecutter recipe** to setup your own Compatibility Patcher in a few minutes, with test scaffolding and packaging
metadata ready for launch.

Documentation is available on `Read The Docs <https://compat-patcher-core.readthedocs.io/en/latest/index.html>`_

Sources are available on `Github <https://github.com/pakal/compat-patcher-core>`_


Which applications currently benefit from this system?

- The Django Web Framework via `Django-Compat-Patcher <https://github.com/pakal/django-compat-patcher>`_
