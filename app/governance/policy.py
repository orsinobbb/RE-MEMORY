ALLOWED_TOOLS={"markdown_handoff"}
def check_tool(name):
    if name not in ALLOWED_TOOLS:raise ValueError("TOOL_NOT_ALLOWED")
