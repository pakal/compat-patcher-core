import sys

from compat_patcher.import_proxifier import (
    install_import_proxifier,
    register_module_alias,
    _is_new_style_proxifier,
)


def test_import_proxifier():

    install_import_proxifier()
    install_import_proxifier()  # idempotent

    register_module_alias("json.tool_alias", "json.tool")
    register_module_alias("mylogging", "logging")
    register_module_alias("mylogging", "logging")
    register_module_alias("infinite_recursion", "infinite_recursion2")
    register_module_alias("infinite_recursion2", "infinite_recursion")
    register_module_alias("unexisting_alias", "unexisting_module")

    fullname = "logging.handlers"
    # print ("ALREADY THERE:", fullname, fullname in sys.modules)

    import json.tool_alias

    assert sys.modules["json.tool_alias"]
    assert json.tool_alias

    fullname = "json.comments"
    # print ("ALREADY THERE:", fullname, fullname in sys.modules)

    fullname = "json.tool"
    # print ("ALREADY THERE:", fullname, fullname in sys.modules)

    import json.tool
    import json.tool

    # if _is_new_style_proxifier:
    # print ("JSON TOOL SPEC loader_state:", json.tool.__spec__.loader_state)

    assert json.tool_alias is json.tool, (json.tool_alias, json.tool)
    assert json.tool.__name__ == "json.tool", json.tool.__name__
    if _is_new_style_proxifier:
        assert json.tool.__spec__.origin == "alias", json.tool.__spec__.origin
        assert json.tool.__spec__.name == "json.tool_alias"
        assert json.tool.__spec__.loader_state["aliased_spec"].name == "json.tool"

    from mylogging import config

    assert config.dictConfig
    assert "logging.config" in sys.modules

    from mylogging.handlers import RotatingFileHandler
    from logging.handlers import RotatingFileHandler as RotatingFileHandlerOriginal

    # print("mylogging led to RotatingFileHandler", RotatingFileHandler)
    assert RotatingFileHandler is RotatingFileHandlerOriginal

    try:
        import infinite_recursion
    except RuntimeError:
        pass
    else:
        raise RuntimeError("Import should have led to infinite recursion")

    try:
        import unexisting_alias
    except ImportError as e:
        assert "unexisting_alias" in str(e), (str(e), vars(e))
        assert "unexisting_module" in str(e), str(e)
    else:
        raise RuntimeError("import error noy raised")

    try:
        import unexisting_module
    except ImportError as e:
        assert "unexisting_alias" not in str(e), str(e)
        assert "unexisting_module" in str(e), str(e)
    else:
        raise RuntimeError("import error noy raised")
