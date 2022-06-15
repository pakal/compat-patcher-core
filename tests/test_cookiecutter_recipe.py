from contextlib import contextmanager
import shlex
import os
import sys
import subprocess
import datetime

from cookiecutter.utils import rmtree

import compat_patcher_core

SOURCE_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@contextmanager
def inside_dir(dirpath):
    """
    Execute code from inside the given directory
    :param dirpath: String, path of the directory the command is being run.
    """
    old_path = os.getcwd()
    try:
        os.chdir(dirpath)
        yield
    finally:
        os.chdir(old_path)


@contextmanager
def bake_in_temp_dir(cookies, **kwargs):
    """
    Delete the temporal directory that is created when executing the tests

    :param cookies: pytest_cookies.Cookies, cookie to be baked and its
    temporal files will be removed
    """
    result = cookies.bake(template=SOURCE_ROOT_DIR, **kwargs)
    try:
        yield result
    finally:
        rmtree(str(result.project))


def run_inside_dir(command, dirpath, **popen_kwargs):
    """
    Run a command from inside a given directory, returning the exit status

    :param command: Command that will be executed
    :param dirpath: String, path of the directory the command is being run.
    """
    with inside_dir(dirpath):
        return subprocess.check_call(shlex.split(command), **popen_kwargs)


def check_output_inside_dir(command, dirpath):
    "Run a command from inside a given directory, returning the command output"
    with inside_dir(dirpath):
        return subprocess.check_output(shlex.split(command))


def test_bake_with_defaults(cookies):
    with bake_in_temp_dir(cookies) as result:
        assert result.project.isdir()
        assert result.exit_code == 0
        assert result.exception is None

        found_toplevel_files = [f.basename for f in result.project.listdir()]
        assert 'setup.py' in found_toplevel_files
        assert 'tox.ini' in found_toplevel_files
        assert 'tests' in found_toplevel_files


def test_bake_and_run_tests(cookies):
    with bake_in_temp_dir(cookies) as result:
        assert result.project.isdir()
        run_inside_dir('python setup.py test', str(result.project)) == 0


def test_bake_withspecialchars_and_run_tests(cookies):
    """Ensure that a `full_name` with double quotes does not break setup.py"""
    with bake_in_temp_dir(cookies, extra_context={'full_name': 'name "quote" name'}) as result:
        assert result.project.isdir()
        run_inside_dir('python setup.py test', str(result.project)) == 0


def test_bake_with_apostrophe_and_run_tests(cookies):
    """Ensure that a `full_name` with apostrophes does not break setup.py"""
    with bake_in_temp_dir(cookies, extra_context={'full_name': "O'connor"}) as result:
        assert result.project.isdir()
        run_inside_dir('python setup.py test', str(result.project)) == 0


def test_using_pytest(cookies):
    with bake_in_temp_dir(cookies) as result:
        assert result.project.isdir()
        # Test the new pytest target - we must help pytest find current compat_patcher_core though
        popen_kwargs = dict(
            env=dict(os.environ,
                     PYTHONPATH=os.path.dirname(os.path.dirname(compat_patcher_core.__file__))))
        run_inside_dir('pytest', str(result.project), **popen_kwargs) == 0
