import sys, os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from compat_patcher_core.readme_generator import generate_readme
from {{ cookiecutter.project_slug }}.registry import patching_registry


def generate_dcp_readme():
    generate_readme(
        input_filename="README.in",
        output_filename="README.rst",
        patching_registry=patching_registry,
    )


if __name__ == "__main__":
    generate_dcp_readme()
    print("DONE")
