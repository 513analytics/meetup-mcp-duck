from openai import AsyncOpenAI
import chainlit as cl
from settings import settings
from mcp import ClientSession
import json

client = AsyncOpenAI(
    api_key=settings.API_KEY,  # litellm proxy virtual key
    base_url=settings.BASE_URL,  # litellm proxy base_url
)

# Instrument the OpenAI client
cl.instrument_openai()

settings = {
    "model": settings.LLM_MODEL,  # model you want to send litellm proxy
    "temperature": 0,
    # ... more settings
}


@cl.on_mcp_connect
async def on_mcp(connection, session: ClientSession):
    # List available tools
    result = await session.list_tools()

    # Process tool metadata
    tools = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        }
        for t in result.tools
    ]

    # Store tools for later use
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = tools
    cl.user_session.set("mcp_tools", mcp_tools)


@cl.step(type="tool")
async def call_tool(tool_use):
    tool_name = tool_use.name
    tool_input = tool_use.input

    current_step = cl.context.current_step
    current_step.name = tool_name

    # Identify which mcp is used
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_name = None

    for connection_name, tools in mcp_tools.items():
        if any(tool.get("name") == tool_name for tool in tools):
            mcp_name = connection_name
            break

    if not mcp_name:
        current_step.output = json.dumps(
            {"error": f"Tool {tool_name} not found in any MCP connection"}
        )
        return current_step.output

    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)

    if not mcp_session:
        current_step.output = json.dumps(
            {"error": f"MCP {mcp_name} not found in any MCP connection"}
        )
        return current_step.output

    try:
        current_step.output = await mcp_session.call_tool(tool_name, tool_input)
    except Exception as e:
        current_step.output = json.dumps({"error": str(e)})

    return current_step.output


@cl.on_message
async def on_message(message: cl.Message):
    response = await client.chat.completions.create(
        messages=[
            {
                "content": "You are a senior data analyst assisting an analyst in a data analysis task operating from a DuckDB database.",
                "role": "system",
            },
            {"content": message.content, "role": "user"},
        ],
        **settings,
    )
    await cl.Message(content=response.choices[0].message.content).send()
