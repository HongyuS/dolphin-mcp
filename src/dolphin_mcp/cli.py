"""
Command-line interface for Dolphin MCP.
"""

import asyncio
import json
import sys
from .utils import parse_arguments
from .client import run_interaction, init_mcp_servers


async def run(user_query, chosen_model_name, config_path, quiet_mode, log_messages_path):
    """
    Run the interaction with the given parameters.
    """
    result = await run_interaction(
        user_query=user_query,
        model_name=chosen_model_name,
        config_path=config_path,
        quiet_mode=quiet_mode,
        log_messages_path=log_messages_path,
        stream=True,
    )
    async for chunk in result:
        data = {"content": chunk}
        sys.stdout.write(f"data: {json.dumps(data, ensure_ascii=False)}\n\n")


async def list_all_tools(config_path, quiet_mode):
    """
    列出所有MCP服务器及其工具列表。

    Args:
        config_path: 配置文件路径
        quiet_mode: 是否静默模式
    """
    servers = await init_mcp_servers(config_path=config_path, quiet_mode=quiet_mode)

    result = {}
    for server_name, client in servers.items():
        # 仅包含name和description字段的工具列表
        filtered_tools = []
        for tool in client.tools:
            # 仅保留name和description字段，并移除这些字段开头和结尾的不可见字符
            filtered_tool = {}
            if "name" in tool:
                filtered_tool["name"] = tool["name"].strip()
            if "description" in tool:
                filtered_tool["description"] = tool["description"].strip()
            filtered_tools.append(filtered_tool)

        result[server_name] = filtered_tools

    # 输出JSON格式的工具列表
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 清理资源
    for client in servers.values():
        await client.stop()


def main():
    """
    Main entry point for the CLI.
    """
    # Check for help flag first
    if "--help" in sys.argv or "-h" in sys.argv:
        print(
            "Usage: dolphin-mcp-cli [--model <name>] [--quiet] [--config <file>] [--log-messages <file>] [--tools] 'your question'"
        )
        print("\nOptions:")
        print("  --model <name>         Specify the model to use")
        print("  --quiet                Suppress intermediate output")
        print("  --config <file>        Specify a custom config file (default: mcp_config.json)")
        print("  --log-messages <file>  Log all LLM interactions to a JSONL file")
        print("  --tools, -t            List all available tools in JSON format")
        print("  --help, -h             Show this help message")
        sys.exit(0)

    chosen_model_name, user_query, quiet_mode, config_path, log_messages_path, list_tools = parse_arguments()

    if list_tools:
        # 如果指定了--tool选项，则列出所有工具并退出
        asyncio.run(list_all_tools(config_path, quiet_mode))
        sys.exit(0)

    if not user_query:
        print("Usage: dolphin-mcp-cli [--model <name>] [--quiet] [--config <file>] [--tools] 'your question'")
        sys.exit(1)

    asyncio.run(
        run(
            user_query=user_query,
            chosen_model_name=chosen_model_name,
            config_path=config_path,
            quiet_mode=quiet_mode,
            log_messages_path=log_messages_path,
        )
    )


if __name__ == "__main__":
    main()
