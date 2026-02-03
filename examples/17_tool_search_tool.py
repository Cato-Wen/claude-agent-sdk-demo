"""
Example 17: Tool Search Tool
============================
演示 Anthropic API 的 Tool Search Tool 功能。

工作原理：
1. 将大部分工具标记为 defer_loading: true（延迟加载）
2. Claude 最初只看到 tool_search_tool 和非延迟工具
3. 当 Claude 需要某个工具时，它会搜索工具目录
4. API 返回匹配的 tool_reference，自动扩展为完整定义
5. Claude 然后调用发现的工具

两种搜索变体：
- regex: Claude 构造正则表达式来搜索
- bm25: Claude 使用自然语言查询搜索

支持的模型/平台：
- Anthropic API: Claude Sonnet 4.5, Opus 4.5 (beta: advanced-tool-use-2025-11-20)
- Vertex AI: 仅 Claude Opus 4.5 (beta: tool-search-tool-2025-10-19)
- Bedrock: 仅 Claude Opus 4.5 (beta: tool-search-tool-2025-10-19)
"""

import anthropic
from anthropic import AnthropicVertex
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载项目根目录的 .env
load_dotenv(Path(__file__).parent.parent / ".env", override=True)


# ============================================================
# 工具定义（这些工具会在实际调用中使用）
# ============================================================
TOOLS = [
    # 1. Tool Search Tool（必须是非延迟的）
    {
        "type": "tool_search_tool_regex_20251119",
        "name": "tool_search_tool_regex"
    },

    # 2. 延迟加载的工具（defer_loading: true）
    {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["city"]
        },
        "defer_loading": True
    },
    {
        "name": "send_email",
        "description": "发送电子邮件给指定收件人",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["to", "subject", "body"]
        },
        "defer_loading": True
    },
    {
        "name": "search_database",
        "description": "在数据库中搜索记录",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "table": {"type": "string"}
            },
            "required": ["query"]
        },
        "defer_loading": True
    }
]


def demo_concept():
    """
    演示 Tool Search Tool 的概念（不需要 API 调用）
    展示请求和响应的结构，帮助理解工作原理。
    """
    print("=" * 70)
    print("Tool Search Tool 工作原理演示")
    print("=" * 70)

    # 1. 请求结构
    print("\n【1. API 请求结构】")
    print("-" * 50)

    request_example = {
        "model": "claude-sonnet-4-5-20250514",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": "北京今天天气怎么样？"}
        ],
        "tools": [
            {
                "type": "tool_search_tool_regex_20251119",
                "name": "tool_search_tool_regex"
                # 注意：没有 defer_loading
            },
            {
                "name": "get_weather",
                "description": "获取指定城市的天气信息",
                "input_schema": {"type": "object", "...": "..."},
                "defer_loading": True  # ← 关键！延迟加载
            },
            {
                "name": "send_email",
                "description": "发送电子邮件",
                "defer_loading": True
            }
        ]
    }
    print(json.dumps(request_example, indent=2, ensure_ascii=False))

    # 2. Claude 初始视角
    print("\n【2. Claude 的初始视角】")
    print("-" * 50)
    print("""
    Claude 最初只能看到：
    +----------------------------------------+
    |  可用工具:                              |
    |  - tool_search_tool_regex              |
    |                                        |
    |  (get_weather, send_email 被隐藏)       |
    +----------------------------------------+
    """)

    # 3. 响应结构
    print("\n【3. API 响应结构（Claude 搜索后）】")
    print("-" * 50)

    response_example = {
        "content": [
            {
                "type": "text",
                "text": "我来搜索天气相关的工具。"
            },
            {
                "type": "server_tool_use",
                "id": "srvtoolu_01ABC123",
                "name": "tool_search_tool_regex",
                "input": {"query": "weather|天气"}
            },
            {
                "type": "tool_search_tool_result",
                "tool_use_id": "srvtoolu_01ABC123",
                "content": {
                    "type": "tool_search_tool_search_result",
                    "tool_references": [
                        {"type": "tool_reference", "tool_name": "get_weather"}
                    ]
                }
            },
            {
                "type": "tool_use",
                "id": "toolu_01XYZ789",
                "name": "get_weather",
                "input": {"city": "北京"}
            }
        ],
        "stop_reason": "tool_use"
    }
    print(json.dumps(response_example, indent=2, ensure_ascii=False))

    # 4. 完整流程图
    print("\n【4. 完整工作流程】")
    print("-" * 50)
    print("""
    +------------------------------------------------------------------+
    |                   Tool Search Tool 工作流程                       |
    +------------------------------------------------------------------+
    |                                                                  |
    |   用户: "北京今天天气怎么样?"                                      |
    |         |                                                        |
    |         v                                                        |
    |   +------------------------------------------+                   |
    |   | Claude 分析: 需要天气工具                 |                   |
    |   | 但是: 可用工具中没有天气工具              |                   |
    |   | 决定: 使用 tool_search_tool 搜索         |                   |
    |   +------------------------------------------+                   |
    |         |                                                        |
    |         v                                                        |
    |   +------------------------------------------+                   |
    |   | server_tool_use:                         |                   |
    |   |   name: tool_search_tool_regex           |                   |
    |   |   input: {"query": "weather"}            |                   |
    |   +------------------------------------------+                   |
    |         |                                                        |
    |         v  (API 服务器端自动处理)                                 |
    |   +------------------------------------------+                   |
    |   | tool_search_tool_result:                 |                   |
    |   |   tool_references:                       |                   |
    |   |     - tool_name: "get_weather"           |                   |
    |   +------------------------------------------+                   |
    |         |                                                        |
    |         v  (get_weather 定义自动加载到上下文)                     |
    |   +------------------------------------------+                   |
    |   | tool_use:                                |                   |
    |   |   name: get_weather                      |                   |
    |   |   input: {"city": "Beijing"}             |                   |
    |   +------------------------------------------+                   |
    |         |                                                        |
    |         v  (你的代码执行工具)                                     |
    |   +------------------------------------------+                   |
    |   | tool_result:                             |                   |
    |   |   {"temperature": 22, "condition": "Sunny"}                  |
    |   +------------------------------------------+                   |
    |         |                                                        |
    |         v                                                        |
    |   Claude: "北京今天天气晴朗, 气温22C..."                          |
    |                                                                  |
    +------------------------------------------------------------------+
    """)

    # 5. 两种搜索变体对比
    print("\n【5. 两种搜索变体】")
    print("-" * 50)
    print("""
    +----------------------------+--------------------------------------+
    |  变体                       |  说明                                |
    +----------------------------+--------------------------------------+
    |  tool_search_tool_regex    |  正则表达式搜索                       |
    |  _20251119                 |  查询示例:                           |
    |                            |  - "weather"                         |
    |                            |  - "get_.*_data"                     |
    |                            |  - "(?i)slack" (不区分大小写)         |
    +----------------------------+--------------------------------------+
    |  tool_search_tool_bm25     |  自然语言搜索 (BM25 算法)             |
    |  _20251119                 |  查询示例:                           |
    |                            |  - "获取天气信息"                     |
    |                            |  - "send a message to user"          |
    +----------------------------+--------------------------------------+
    """)

    # 6. 为什么使用
    print("\n【6. 为什么使用 Tool Search Tool?】")
    print("-" * 50)
    print("""
    问题:
    |-- 50 个工具定义 = 10,000-20,000 tokens
    |-- 上下文窗口被工具定义占用
    +-- 超过 30-50 个工具时, Claude 选择准确性下降

    解决方案: Tool Search Tool
    |-- 大部分工具设置 defer_loading: true
    |-- Claude 按需搜索, 只加载需要的工具
    |-- 每次搜索返回 3-5 个最相关的工具
    +-- 支持多达 10,000 个工具!
    """)

    # 7. 代码示例
    print("\n【7. Python 代码示例】")
    print("-" * 50)
    print('''
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250514",
    betas=["advanced-tool-use-2025-11-20"],  # 必需！
    max_tokens=1024,
    messages=[{"role": "user", "content": "北京天气怎么样？"}],
    tools=[
        # Tool Search Tool (不能有 defer_loading)
        {
            "type": "tool_search_tool_regex_20251119",
            "name": "tool_search_tool_regex"
        },
        # 延迟加载的工具
        {
            "name": "get_weather",
            "description": "获取天气",
            "input_schema": {...},
            "defer_loading": True  # ← 关键
        }
    ]
)

# 处理响应中的不同 block 类型
for block in response.content:
    if block.type == "server_tool_use":
        print(f"Claude 搜索工具: {block.input}")
    elif block.type == "tool_search_tool_result":
        print(f"发现工具: {block.content.tool_references}")
    elif block.type == "tool_use":
        print(f"调用工具: {block.name}({block.input})")
''')


def get_client_and_config():
    """根据环境变量选择正确的客户端和配置"""
    if os.getenv("ANTHROPIC_API_KEY"):
        print("使用 Anthropic API")
        return (
            anthropic.Anthropic(),
            "claude-sonnet-4-5-20250514",
            "advanced-tool-use-2025-11-20"
        )

    if os.getenv("CLAUDE_CODE_USE_VERTEX") == "1":
        print("使用 Google Vertex AI")
        return (
            AnthropicVertex(
                project_id=os.getenv("ANTHROPIC_VERTEX_PROJECT_ID"),
                region=os.getenv("CLOUD_ML_REGION", "us-east5")
            ),
            "claude-sonnet-4-5@20250929",  # Sonnet 4.5 正确的版本日期
            "tool-search-tool-2025-10-19"
        )

    return None, None, None


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """模拟执行工具并返回结果"""
    if tool_name == "get_weather":
        city = tool_input.get("city", "Unknown")
        return json.dumps({
            "city": city,
            "temperature": 22,
            "unit": "celsius",
            "condition": "Sunny",
            "humidity": 45,
            "wind": "Northeast 3m/s"
        }, ensure_ascii=False)

    elif tool_name == "send_email":
        return json.dumps({"status": "sent", "message_id": "msg_12345"})

    elif tool_name == "search_database":
        return json.dumps({"results": [], "count": 0})

    return json.dumps({"error": "Unknown tool"})


def demo_api_call():
    """实际调用 API 演示 Tool Search Tool - 完整工具调用循环"""
    print("\n" + "=" * 70)
    print("实际 API 调用演示 (完整工具调用循环)")
    print("=" * 70)

    client, model, beta_header = get_client_and_config()

    if client is None:
        print("\n[!] 跳过实际 API 调用")
        print("    需要设置 ANTHROPIC_API_KEY 环境变量")
        print("    或者在 Vertex AI 上启用 Claude Opus 4.5")
        return

    print(f"\n模型: {model}")
    print(f"Beta: {beta_header}")

    user_message = "北京今天天气怎么样?"
    messages = [{"role": "user", "content": user_message}]

    print(f"\n用户: {user_message}")
    print("-" * 50)

    turn = 0
    max_turns = 5  # 防止无限循环

    try:
        while turn < max_turns:
            turn += 1
            print(f"\n--- 第 {turn} 轮 API 调用 ---")

            response = client.beta.messages.create(
                model=model,
                betas=[beta_header],
                max_tokens=1024,
                messages=messages,
                tools=TOOLS
            )

            print(f"stop_reason: {response.stop_reason}")

            # 解析响应内容
            tool_calls = []
            for i, block in enumerate(response.content):
                print(f"\n  [{i+1}] {block.type}")

                if block.type == "text":
                    # 处理可能的编码问题（Windows 终端不支持某些 Unicode 字符）
                    text = block.text.encode('gbk', errors='replace').decode('gbk')
                    print(f"      {text[:200]}..." if len(text) > 200 else f"      {text}")

                elif block.type == "server_tool_use":
                    print(f"      Tool Search 查询: {block.input}")

                elif block.type == "tool_search_tool_result":
                    if hasattr(block.content, 'tool_references'):
                        refs = [ref.tool_name for ref in block.content.tool_references]
                        print(f"      发现工具: {refs}")

                elif block.type == "tool_use":
                    print(f"      调用工具: {block.name}")
                    print(f"      参数: {json.dumps(block.input, ensure_ascii=False)}")
                    tool_calls.append(block)

            # 如果没有工具调用，对话结束
            if response.stop_reason == "end_turn":
                print("\n" + "=" * 50)
                print("对话结束!")
                break

            # 如果有工具调用，执行工具并继续
            if response.stop_reason == "tool_use" and tool_calls:
                # 添加 assistant 消息
                messages.append({"role": "assistant", "content": response.content})

                # 执行每个工具调用并收集结果
                tool_results = []
                for tool_call in tool_calls:
                    result = execute_tool(tool_call.name, tool_call.input)
                    print(f"\n  >> 执行 {tool_call.name}, 返回: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result
                    })

                # 添加工具结果
                messages.append({"role": "user", "content": tool_results})

            else:
                # 其他情况，结束循环
                break

    except Exception as e:
        print(f"\n[X] API 调用失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    # 1. 先演示概念（不需要 API）
    # demo_concept()

    # 2. 尝试实际 API 调用
    demo_api_call()

    print("\n" + "=" * 70)
    print("演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
