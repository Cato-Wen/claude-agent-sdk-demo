"""
Example 19: Tool Approval Demo (can_use_tool)
=============================================
演示如何使用 can_use_tool 回调实现工具使用审批。
当 Claude 想要使用工具时，会触发回调请求用户批准。
"""

import asyncio
import sys
import io
import os

# 设置流超时时间（毫秒）- 可以设置很大的值实现"永久"等待
# 默认 60000ms (60秒)，这里设置为 300000ms (5分钟)
os.environ["CLAUDE_CODE_STREAM_CLOSE_TIMEOUT"] = "300000"

# 设置 stdout 编码为 utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.append("..")

from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import (
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)
from utils.config import check_api_key, PROJECT_ROOT

# 用户输入超时时间（秒）- 从环境变量读取，保持一致
# 稍微减少一点以确保在流关闭前返回
INPUT_TIMEOUT = int(os.environ.get("CLAUDE_CODE_STREAM_CLOSE_TIMEOUT", "300000")) / 1000 - 5


async def can_use_tool(
    tool_name: str, input_data: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """
    工具使用审批回调。
    当 Claude 想要使用任何工具时，都会触发此回调。
    """
    print("\n" + "=" * 60)
    print(f"[TOOL] 工具审批请求")
    print("=" * 60)
    print(f"工具名称: {tool_name}")

    # 根据不同工具类型显示不同信息
    if tool_name == "Bash":
        command = input_data.get("command", "")
        description = input_data.get("description", "无描述")
        print(f"命令: {command}")
        print(f"描述: {description}")
    elif tool_name == "Read":
        print(f"文件路径: {input_data.get('file_path', '未知')}")
    elif tool_name == "Write":
        print(f"文件路径: {input_data.get('file_path', '未知')}")
        content = input_data.get("content", "")
        print(f"内容预览: {content[:100]}..." if len(content) > 100 else f"内容: {content}")
    elif tool_name == "Edit":
        print(f"文件路径: {input_data.get('file_path', '未知')}")
        print(f"旧内容: {input_data.get('old_string', '')[:50]}...")
        print(f"新内容: {input_data.get('new_string', '')[:50]}...")
    elif tool_name == "Glob":
        print(f"模式: {input_data.get('pattern', '未知')}")
    elif tool_name == "Grep":
        print(f"搜索模式: {input_data.get('pattern', '未知')}")
        print(f"路径: {input_data.get('path', '当前目录')}")
    elif tool_name == "AskUserQuestion":
        # 处理澄清问题
        print("Claude 想要向您提问:")
        questions = input_data.get("questions", [])
        for q in questions:
            print(f"  - {q.get('question', '')}")
        # 自动允许 AskUserQuestion
        return PermissionResultAllow(updated_input=input_data)
    else:
        print(f"输入参数: {input_data}")

    print("-" * 60)
    print(f"[!] 请在 {INPUT_TIMEOUT} 秒内输入，否则将自动拒绝")

    # 带超时的异步输入
    async def async_input_with_timeout(prompt_text: str, timeout: float = INPUT_TIMEOUT) -> str | None:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(input, prompt_text),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print("\n[TIMEOUT] 输入超时，自动拒绝")
            return None

    # 获取用户审批
    while True:
        response = await async_input_with_timeout("是否允许此操作? (y=允许 / n=拒绝 / m=修改后允许): ")

        if response is None:
            return PermissionResultDeny(message="用户输入超时")

        response = response.strip().lower()

        if response == "y":
            print("[OK] 已批准")
            return PermissionResultAllow(updated_input=input_data)

        elif response == "n":
            reason = await async_input_with_timeout("请输入拒绝原因 (可选，直接回车跳过): ")
            if reason is None or not reason.strip():
                reason = "用户拒绝了此操作"
            print(f"[DENIED] 已拒绝: {reason}")
            return PermissionResultDeny(message=reason)

        elif response == "m":
            # 允许用户修改输入
            if tool_name == "Bash":
                new_command = await async_input_with_timeout(
                    f"请输入新命令 (原命令: {input_data.get('command', '')}): "
                )
                if new_command is None:
                    return PermissionResultDeny(message="用户输入超时")
                if new_command.strip():
                    modified_input = {**input_data, "command": new_command.strip()}
                    print(f"[OK] 已批准修改后的命令: {new_command.strip()}")
                    return PermissionResultAllow(updated_input=modified_input)
                else:
                    print("命令不能为空，请重新选择")
            else:
                print("此工具暂不支持修改，请选择 y 或 n")
        else:
            print("无效输入，请输入 y、n 或 m")


async def dummy_hook(input_data, tool_use_id, context):
    """
    必要的 workaround：保持流的打开状态以支持 can_use_tool。
    没有这个 hook，流会在权限回调被调用之前关闭。
    """
    return {"continue_": True}


async def prompt_stream():
    """
    使用流式输入模式（can_use_tool 需要此模式）。
    """
    yield {
        "type": "user",
        "message": {
            "role": "user",
            "content": "请执行以下操作：1. 列出 examples 目录下的 Python 文件 2. 读取第一个文件的前10行 3. 在 /tmp 目录创建一个测试文件并删除它",
        },
    }


async def main():
    """演示工具使用审批功能。"""
    check_api_key()

    print("=" * 60)
    print("工具审批 Demo")
    print("=" * 60)
    print("此 demo 展示如何使用 can_use_tool 实现工具使用审批。")
    print("当 Claude 想要使用工具时，您需要手动批准或拒绝。")
    print(f"[注意] 每次审批需在 {INPUT_TIMEOUT} 秒内完成，否则流会关闭")
    print("=" * 60 + "\n")

    options = ClaudeAgentOptions(
        # 不设置 allowed_tools，让所有工具都需要审批
        # 或使用 permission_mode="default" 来要求审批
        cwd=str(PROJECT_ROOT),
        can_use_tool=can_use_tool,
        # 必须添加 PreToolUse hook 来保持流的打开状态
        hooks={
            "PreToolUse": [HookMatcher(matcher=None, hooks=[dummy_hook])]
        },
    )

    print("正在启动 Claude Agent...")
    print("-" * 40)

    async for message in query(
        prompt=prompt_stream(),
        options=options,
    ):
        if hasattr(message, "result"):
            print("\n" + "=" * 60)
            print("[RESULT] 最终结果:")
            print("=" * 60)
            print(message.result)


if __name__ == "__main__":
    asyncio.run(main())
