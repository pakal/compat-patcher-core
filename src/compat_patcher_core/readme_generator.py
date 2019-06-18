from __future__ import absolute_import, print_function, unicode_literals

from functools import reduce
from io import open

from compat_patcher_core.utilities import detuplify_software_version


def make_table(grid):
    """
    Borrowed from http://stackoverflow.com/a/12539081/5088990
    :param grid: List of lists
    :return:
    """

    def _table_div(num_cols, col_width, header_flag):
        if header_flag == 1:
            return num_cols * ("+" + (col_width) * "=") + "+\n"
        else:
            return num_cols * ("+" + (col_width) * "-") + "+\n"

    def _normalize_cell(string, length):
        return string + ((length - len(string)) * " ")

    cell_width = 2 + max(
        reduce(lambda x, y: x + y, [[len(item) for item in row] for row in grid], [])
    )
    num_cols = len(grid[0])
    rst = _table_div(num_cols, cell_width, 0)
    header_flag = 1
    for row in grid:
        rst = (
            rst
            + "| "
            + "| ".join([_normalize_cell(x, cell_width - 1) for x in row])
            + "|\n"
        )
        rst = rst + _table_div(num_cols, cell_width, header_flag)
        header_flag = 0
    return rst


def _create_fixer_list(all_fixers, grid):
    """
    Creates a list for the fixers table.
    Each fixer creates a list of its name, its min version and its max version if it exists.
    Ex: ["fix_deletion_http_request_HttpRequest_raw_post_data", "1.6", ""]
    """
    for fixer in all_fixers:
        format_tuple = (
            fixer["fixer_explanation"].replace("\n", "").strip(),
            fixer["fixer_callable"].__name__,
        )
        grid.append(
            [
                "**{}** (:code:`{}`)".format(*format_tuple),
                fixer["fixer_family"],
                detuplify_software_version(fixer["fixer_applied_from_version"]) or "",
                detuplify_software_version(fixer["fixer_applied_upto_version"]) or "",
            ]
        )


def _create_headers(grid):
    table_headers = ["Fixer and its ID", "Fixer family", "Min version", "Max version"]
    grid.append(table_headers)


def _make_rst_table(patching_registry):
    all_fixers = patching_registry.get_all_fixers()
    all_fixers.sort(key=lambda f: (f["fixer_reference_version"], f["fixer_id"]))
    grid = []
    _create_headers(grid=grid)
    _create_fixer_list(all_fixers, grid=grid)
    rst_table = make_table(grid=grid)
    return rst_table


def generate_readme(input_filename, output_filename, patching_registry):
    """
    Take an input file in RESTRUCTUREDTEXT format, append the table of available fixers to it,
    and generate the actual readme.
    """
    patching_registry.populate()

    with open(input_filename, mode="r", encoding="utf-8") as readme_manual:
        readme_manual_content = readme_manual.read()

    result = readme_manual_content + "\n\n"
    result += "Table of fixers\n===============\n\n"
    result += "There are currently {} available fixers.\n\n".format(
        len(patching_registry.get_all_fixers())
    )
    result += _make_rst_table(patching_registry)

    with open(output_filename, mode="w", encoding="utf-8") as readme_final:
        readme_final.write(result)
