from __future__ import absolute_import, print_function, unicode_literals

from docutils.core import publish_parts

from compat_patcher_core.readme_generator import generate_readme
from dummy_fixers import patching_registry


def test_generate_readme(tmp_path):

    readme_in_file = tmp_path / "Readme.in"

    readme_in_file.write_text("THIS IS A README\n####################\n\n")

    readme_out_file = tmp_path / "Readme.txt"

    print(readme_in_file, readme_out_file)
    generate_readme(str(readme_in_file), str(readme_out_file), patching_registry)

    content = readme_out_file.read_text()

    html_body = publish_parts(source=content, writer_name="html4css1")["html_body"]

    assert "THIS IS A README" in html_body
    assert "available fixers" in html_body
    assert "<table" in html_body
