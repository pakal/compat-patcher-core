#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # security

from setuptools import setup, find_packages

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


readme_filename = "README.rst"
if not os.path.exists("README.rst"):
    raise RuntimeError("%s not found, have you run generate_readme.py first?" % readme_filename)


classifiers = [
    # Add your Trove classifiers here
]

packages = find_packages(where="src")

setup(
    name="{{ cookiecutter.project_name }}",
    version=read_file("VERSION"),
    author="{{ cookiecutter.full_name.replace('\"', '\\\"') }}",
    author_email='{{ cookiecutter.email }}',
    url='https://github.com/pakal/compat-patcher',
    license="MIT",
    platforms=["any"],
    description="{{ cookiecutter.project_short_description }}",
    classifiers=classifiers,
    long_description=read_file(readme_filename),
    package_dir={"": "src"},
    packages=packages,
    install_requires=["compat-patcher-core"],
    extras_require={},
)
