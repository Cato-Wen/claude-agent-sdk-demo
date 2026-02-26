"""
Example 18: User Isolation Demo (Full Sandboxing)
=================================================
演示如何使用 Claude Agent SDK 实现多用户隔离。

隔离机制：
1. cwd 目录隔离 - 每个用户有独立的工作目录
2. can_use_tool 权限控制 - 验证文件路径、过滤危险命令
3. Hooks 审计日志 - 记录所有操作

演示场景：
1. Alice 创建文件 → 成功
2. Bob 尝试读取 Alice 的文件 → 被拒绝
3. Bob 创建自己的文件 → 成功
4. Alice 尝试执行危险命令 → 被拒绝
5. Alice 使用 code-reviewer Skill 审查代码 → 成功（Skill + 隔离）
6. Bob 使用 doc-generator Skill 生成文档 → 成功（Skill + 隔离）
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Any

sys.path.append("..")

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    SystemMessage,
)
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny
from utils.config import check_api_key, PROJECT_ROOT
from utils.message_tracker import MessageTracker


# ============================================================
# 配置
# ============================================================
SANDBOX_ROOT = Path(PROJECT_ROOT) / "sandboxes"
SANDBOX_ROOT.mkdir(exist_ok=True)


# ============================================================
# 审计日志
# ============================================================
class AuditLogger:
    """简单的审计日志记录器"""

    def __init__(self):
        self.logs: list[dict] = []

    def log(self, user_id: str, action: str, details: dict, allowed: bool = True):
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user": user_id,
            "action": action,
            "allowed": "Y" if allowed else "N",
            "details": details,
        }
        self.logs.append(entry)
        status = "[ALLOWED]" if allowed else "[DENIED]"
        print(f"  [{entry['timestamp']}] [{user_id}] {action} {status}")
        if details:
            for k, v in details.items():
                print(f"    {k}: {v}")

    def print_summary(self):
        print("\n" + "=" * 60)
        print("审计日志摘要")
        print("=" * 60)
        for entry in self.logs:
            print(f"[{entry['timestamp']}] {entry['user']:10} | {entry['allowed']} {entry['action']}")


# 全局审计日志
audit_logger = AuditLogger()


# ============================================================
# 用户隔离会话
# ============================================================
class IsolatedUserSession:
    """
    隔离的用户会话。

    每个用户有：
    - 独立的工作目录 (workspace)
    - 独立的权限检查 (can_use_tool)
    - 独立的审计钩子 (hooks)
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.workspace = SANDBOX_ROOT / user_id
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.client: ClaudeSDKClient | None = None

        print(f"\n[创建用户会话] {user_id}")
        print(f"  工作目录: {self.workspace}")

    async def _permission_handler(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        context: Any
    ) -> PermissionResultAllow | PermissionResultDeny:
        """
        权限处理器 - 核心隔离逻辑

        检查：
        1. 文件操作是否在用户工作区内
        2. Bash 命令是否安全
        """

        # ========== 文件操作检查 ==========
        if tool_name in ["Read", "Write", "Edit"]:
            file_path = input_data.get("file_path", "")

            # 解析路径
            try:
                # 处理相对路径
                if not os.path.isabs(file_path):
                    resolved = (self.workspace / file_path).resolve()
                else:
                    resolved = Path(file_path).resolve()

                workspace_resolved = self.workspace.resolve()

                # 检查是否在工作区内
                if not str(resolved).startswith(str(workspace_resolved)):
                    audit_logger.log(
                        self.user_id,
                        f"{tool_name} (路径越界)",
                        {"path": file_path, "resolved": str(resolved)},
                        allowed=False
                    )
                    return PermissionResultDeny(
                        message=f"访问被拒绝: 路径 '{file_path}' 在您的工作区外",
                        interrupt=False
                    )

                audit_logger.log(
                    self.user_id,
                    tool_name,
                    {"path": str(resolved)},
                    allowed=True
                )

            except Exception as e:
                audit_logger.log(
                    self.user_id,
                    f"{tool_name} (路径错误)",
                    {"path": file_path, "error": str(e)},
                    allowed=False
                )
                return PermissionResultDeny(
                    message=f"路径解析错误: {e}",
                    interrupt=False
                )

        # ========== Bash 命令检查 ==========
        elif tool_name == "Bash":
            command = input_data.get("command", "")

            # 危险命令模式
            dangerous_patterns = [
                "rm -rf",
                "sudo",
                "chmod 777",
                "> /dev/",
                "dd if=",
                "mkfs",
                ":(){:|:&};:",  # fork bomb
                "curl | bash",
                "wget | bash",
            ]

            for pattern in dangerous_patterns:
                if pattern in command:
                    audit_logger.log(
                        self.user_id,
                        "Bash (危险命令)",
                        {"command": command, "pattern": pattern},
                        allowed=False
                    )
                    return PermissionResultDeny(
                        message=f"危险命令被阻止: 包含 '{pattern}'",
                        interrupt=False
                    )

            # 检查命令是否尝试访问其他用户目录
            other_users = [d.name for d in SANDBOX_ROOT.iterdir() if d.is_dir() and d.name != self.user_id]
            for other_user in other_users:
                other_path = str(SANDBOX_ROOT / other_user)
                if other_path in command:
                    audit_logger.log(
                        self.user_id,
                        "Bash (访问其他用户)",
                        {"command": command, "target_user": other_user},
                        allowed=False
                    )
                    return PermissionResultDeny(
                        message=f"禁止访问其他用户的目录: {other_user}",
                        interrupt=False
                    )

            audit_logger.log(
                self.user_id,
                "Bash",
                {"command": command[:50] + "..." if len(command) > 50 else command},
                allowed=True
            )

        # ========== Skill 调用检查 ==========
        elif tool_name == "Skill":
            skill_name = input_data.get("skill", "unknown")
            audit_logger.log(
                self.user_id,
                f"Skill ({skill_name})",
                {"skill": skill_name, "args": input_data.get("args", "")},
                allowed=True
            )

        # ========== 其他工具 ==========
        else:
            audit_logger.log(
                self.user_id,
                tool_name,
                {},
                allowed=True
            )

        return PermissionResultAllow(updated_input=input_data)

    async def _pre_tool_hook(
        self,
        input_data: dict[str, Any],
        tool_use_id: str | None,
        context: Any
    ) -> dict[str, Any]:
        """工具执行前钩子 - 用于额外的审计"""
        # 这里可以添加更多的预检查逻辑
        return {}

    async def _post_tool_hook(
        self,
        input_data: dict[str, Any],
        tool_use_id: str | None,
        context: Any
    ) -> dict[str, Any]:
        """工具执行后钩子 - 记录结果"""
        tool_name = input_data.get("tool_name", "unknown")
        # 可以在这里记录工具执行结果
        return {}

    def get_options(self) -> ClaudeAgentOptions:
        """获取用户专属的配置选项"""
        return ClaudeAgentOptions(
            cwd=str(self.workspace),
            # 不设置 allowed_tools，使用can_use_tool检查tool的使用
            setting_sources=["project"],  # 加载 .claude/skills/ 下的 Skill 定义
            permission_mode="default",  # 必须用 default 才能触发 can_use_tool 回调！
            can_use_tool=self._permission_handler,
            hooks={
                "PreToolUse": [HookMatcher(hooks=[self._pre_tool_hook])],
                "PostToolUse": [HookMatcher(hooks=[self._post_tool_hook])],
            },
            # stderr=lambda line: print(f"  [STDERR/{self.user_id}] {line}") if any(kw in line.lower() for kw in ["permission", "can_use", "stdio", "tool_name", "warn", "error"]) else None,
            # extra_args={"debug-to-stderr": None},
        )

    async def execute(self, prompt: str) -> str:
        """执行用户请求"""
        options = self.get_options()
        result_text = ""

        print(f"\n[{self.user_id}] 执行请求: {prompt[:50]}...")
        print("-" * 40)

        # 创建消息跟踪器
        tracker = MessageTracker(name=f"isolation_{self.user_id}")

        try:
            async with ClaudeSDKClient(options=options) as client:
                self.client = client
                await client.query(prompt)

                async for message in client.receive_response():
                    # 跟踪每条消息（保存到 JSON）
                    tracker.track(message)

                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                result_text += block.text
                            elif isinstance(block, ToolUseBlock):
                                print(f"  [工具调用] {block.name}")

                    elif isinstance(message, ResultMessage):
                        if message.result:
                            result_text = message.result

        except Exception as e:
            result_text = f"执行错误: {e}"
            print(f"  [错误] {e}")

        # 只保存到 JSON，不打印摘要
        tracker.save()

        return result_text


# ============================================================
# 演示场景
# ============================================================
async def demo_scenario_1_alice_creates_file(alice: IsolatedUserSession):
    """场景 1: Alice 创建文件"""
    print("\n" + "=" * 60)
    print("场景 1: Alice 在自己的目录创建文件")
    print("=" * 60)

    result = await alice.execute(
        "请在当前目录创建一个名为 secret.txt 的文件，内容为 'Alice 的秘密数据: ABC123'"
    )

    print(f"\n结果: {result[:200] if result else '(无输出)'}")

    # 验证文件是否创建
    secret_file = alice.workspace / "secret.txt"
    if secret_file.exists():
        print(f"\n验证: 文件已创建于 {secret_file}")
        print(f"  内容: {secret_file.read_text(encoding='utf-8')}")
    else:
        print("\n验证: 文件未创建")


async def demo_scenario_2_bob_reads_alice_file(bob: IsolatedUserSession, alice: IsolatedUserSession):
    """场景 2: Bob 尝试读取 Alice 的文件"""
    print("\n" + "=" * 60)
    print("场景 2: Bob 尝试读取 Alice 的文件 (应被拒绝)")
    print("=" * 60)

    # Bob 尝试直接读取 Alice 的文件
    alice_secret = alice.workspace / "secret.txt"

    result = await bob.execute(
        f"请读取文件: {alice_secret}"
    )

    print(f"\n结果: {result[:200] if result else '(无输出)'}")


async def demo_scenario_3_bob_creates_own_file(bob: IsolatedUserSession):
    """场景 3: Bob 创建自己的文件"""
    print("\n" + "=" * 60)
    print("场景 3: Bob 在自己的目录创建文件")
    print("=" * 60)

    result = await bob.execute(
        "请创建一个名为 my_data.txt 的文件，内容为 'Bob 的数据: XYZ789'"
    )

    print(f"\n结果: {result[:200] if result else '(无输出)'}")

    # 验证
    bob_file = bob.workspace / "my_data.txt"
    if bob_file.exists():
        print(f"\n验证: 文件已创建于 {bob_file}")


async def demo_scenario_4_alice_dangerous_command(alice: IsolatedUserSession):
    """场景 4: Alice 尝试执行危险命令"""
    print("\n" + "=" * 60)
    print("场景 4: Alice 尝试执行危险命令 (应被拒绝)")
    print("=" * 60)

    result = await alice.execute(
        "请执行命令: rm -rf ./logs"
    )

    print(f"\n结果: {result[:200] if result else '(无输出)'}")


async def demo_scenario_5_bob_access_alice_via_bash(bob: IsolatedUserSession, alice: IsolatedUserSession):
    """场景 5: Bob 尝试通过 Bash 访问 Alice 的目录"""
    print("\n" + "=" * 60)
    print("场景 5: Bob 尝试通过 Bash 命令访问 Alice 的目录 (应被拒绝)")
    print("=" * 60)

    result = await bob.execute(
        f"请执行命令: cat {alice.workspace}/secret.txt"
    )

    print(f"\n结果: {result[:200] if result else '(无输出)'}")


async def demo_scenario_6_alice_uses_skill(alice: IsolatedUserSession):
    """场景 6: Alice 使用 code-reviewer Skill 审查自己的代码"""
    print("\n" + "=" * 60)
    print("场景 6: Alice 使用 code-reviewer Skill 审查代码")
    print("=" * 60)

    # 先让 Alice 创建一个 Python 文件供审查
    await alice.execute(
        "请创建一个名为 app.py 的文件，内容如下:\n"
        "import os\n"
        "password = '123456'\n"
        "def get_data(sql):\n"
        "    query = 'SELECT * FROM users WHERE id=' + sql\n"
        "    return query\n"
    )

    # 使用 code-reviewer Skill 审查
    result = await alice.execute(
        "Run /code-reviewer on the file app.py in the current directory"
    )

    print(f"\n审查结果: {result[:500] if result else '(无输出)'}")


async def demo_scenario_7_bob_uses_skill(bob: IsolatedUserSession):
    """场景 7: Bob 使用 doc-generator Skill 为自己的代码生成文档"""
    print("\n" + "=" * 60)
    print("场景 7: Bob 使用 doc-generator Skill 生成文档")
    print("=" * 60)

    # 先让 Bob 创建一个 Python 文件
    await bob.execute(
        "请创建一个名为 utils.py 的文件，内容如下:\n"
        "def add(a, b):\n"
        "    return a + b\n\n"
        "def multiply(a, b):\n"
        "    return a * b\n\n"
        "class Calculator:\n"
        "    def __init__(self):\n"
        "        self.history = []\n"
        "    def calc(self, op, a, b):\n"
        "        if op == 'add':\n"
        "            result = add(a, b)\n"
        "        else:\n"
        "            result = multiply(a, b)\n"
        "        self.history.append(result)\n"
        "        return result\n"
    )

    # 使用 doc-generator Skill 生成文档
    result = await bob.execute(
        "Run /doc-generator on the file utils.py in the current directory"
    )

    print(f"\n文档结果: {result[:500] if result else '(无输出)'}")


async def demo_isolation_summary(alice: IsolatedUserSession, bob: IsolatedUserSession):
    """展示隔离状态摘要"""
    print("\n" + "=" * 60)
    print("用户隔离状态摘要")
    print("=" * 60)

    print(f"\nAlice 的工作区: {alice.workspace}")
    alice_files = list(alice.workspace.glob("*"))
    print(f"  文件: {[f.name for f in alice_files]}")

    print(f"\nBob 的工作区: {bob.workspace}")
    bob_files = list(bob.workspace.glob("*"))
    print(f"  文件: {[f.name for f in bob_files]}")

async def main():
    """运行用户隔离演示"""
    check_api_key()

    print("\n" + "#" * 60)
    print("# Claude Agent SDK - 用户隔离演示 (Full Sandboxing)")
    print(f"# 沙箱根目录: {SANDBOX_ROOT}")
    print("#" * 60)

    # 创建两个用户的隔离会话
    alice = IsolatedUserSession("alice")
    bob = IsolatedUserSession("bob")

    # 运行演示场景
    await demo_scenario_1_alice_creates_file(alice)
    # await demo_scenario_2_bob_reads_alice_file(bob, alice)
    # await demo_scenario_3_bob_creates_own_file(bob)
    # await demo_scenario_4_alice_dangerous_command(alice)
    # await demo_scenario_5_bob_access_alice_via_bash(bob, alice)

    # await demo_scenario_6_alice_uses_skill(alice)
    # await demo_scenario_7_bob_uses_skill(bob)

    # 显示摘要
    await demo_isolation_summary(alice, bob)

    # 打印审计日志
    audit_logger.print_summary()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
