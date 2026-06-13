import pytest

from aios.autonomy import ActionType
from aios.tools import Tool, ToolRegistry


def test_register_and_get():
    reg = ToolRegistry()
    tool = Tool(name="publish_post",
                action_type=ActionType("marketing", "social.publish_post"),
                run=lambda **kw: {"published": True})
    reg.register(tool)
    assert reg.get("publish_post") is tool


def test_readonly_tool_has_no_action_type():
    reg = ToolRegistry()
    tool = Tool(name="read_insights", action_type=None, readonly=True,
                run=lambda **kw: {"reach": 1000})
    reg.register(tool)
    assert reg.get("read_insights").readonly is True


def test_duplicate_name_raises():
    reg = ToolRegistry()
    tool = Tool(name="dup", action_type=None, readonly=True, run=lambda **kw: None)
    reg.register(tool)
    with pytest.raises(ValueError):
        reg.register(tool)


def test_unknown_tool_raises():
    reg = ToolRegistry()
    with pytest.raises(KeyError):
        reg.get("missing")
