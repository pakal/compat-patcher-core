#!/usr/bin/env python

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # security

from setuptools import setup, find_packages

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def read_file(fname):
    if not os.path.isabs(fname):
        fname = os.path.join(ROOT_DIR, fname)
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


classifiers = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Developers
Intended Audience :: Information Technology
License :: OSI Approved :: MIT License
Natural Language :: English
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
Programming Language :: Python :: 3.10
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
Operating System :: MacOS :: MacOS X
"""


needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
setup_requires = ["pytest-runner"] if needs_pytest else []

setup(
    name="compat-patcher-core",
    version=read_file("VERSION"),
    author="Pascal Chambon & others",
    author_email="pythoniks@gmail.com",
    url="https://github.com/pakal/compat-patcher-core",
    license="MIT",
    platforms=["any"],
    description="A patcher system to allow easy and lasting API compatibility.",
    classifiers=filter(None, classifiers.split("\n")),
    long_description=read_file("README.rst"),
    package_dir={"": "src"},
    packages=["compat_patcher_core"],
    install_requires=["six"],
    extras_require={
        "build_sphinx": ["sphinx", "sphinx_rtd_theme"],
        "run_pylint": ["pylint", "pylint-quotes"],
    },
    setup_requires=setup_requires,
    tests_require=[
        # Beware, keep in sync with requirements.txt
        "pytest",
        "pytest-cov",
        "docutils",
    ],
)
