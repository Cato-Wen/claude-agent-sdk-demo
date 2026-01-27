# Code Execution Examples

使用 Claude Agent SDK 实现代码执行功能的示例。

## 文件说明

| 文件 | 复杂度 | 说明 |
|------|--------|------|
| `13_code_execution.py` | 基础 | 简单的代码执行演示 |
| `14_sandboxed_code_execution.py` | 中级 | 带沙箱环境的代码执行 |
| `15_code_execution_complete.py` | 高级 | 完整框架，类似 Anthropic API |

## 快速开始

### 基础用法

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def run_code():
    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Write", "Read"],
        permission_mode="acceptEdits",
    )

    prompt = """
    Write and execute Python code that calculates prime numbers from 1 to 50.
    Save the code to primes.py and run it.
    """

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(message.result)
```

### 使用 CodeExecutor 类 (高级)

```python
from examples.code_execution_complete import CodeExecutor, CodeExecutionRequest

async def main():
    # 创建执行器
    executor = CodeExecutor(session_id="my_session")

    # 执行代码
    result = await executor.execute(CodeExecutionRequest(
        code='''
print("Hello, World!")
for i in range(5):
    print(f"Number: {i}")
'''
    ))

    print(f"Status: {result.status}")
    print(f"Output: {result.stdout}")
    print(f"Files: {result.files_created}")
```

### 执行自然语言任务

```python
result = await executor.execute(CodeExecutionRequest(
    task="创建一个生成随机密码的脚本，生成10个16位密码并保存到文件"
))
```

## 与 Anthropic API code_execution 对比

| 功能 | Anthropic API | Claude Agent SDK |
|------|---------------|------------------|
| 执行环境 | 云端沙箱 | 本地机器 |
| 隔离性 | 完全隔离 | 需自行实现 |
| Skills 支持 | ✅ pptx/xlsx/docx/pdf | ❌ |
| 网络访问 | 受限 | 完全访问 |
| 文件大小限制 | 有 | 无 |
| 执行时间限制 | 有 | 可配置 |
| 费用 | 按使用计费 | 仅 API 调用费用 |

## 运行示例

```bash
cd examples

# 基础示例
python 13_code_execution.py

# 沙箱示例
python 14_sandboxed_code_execution.py

# 完整框架示例
python 15_code_execution_complete.py
```

## 注意事项

1. **安全性**: 代码在本地执行，没有沙箱隔离，请谨慎使用
2. **权限**: 使用 `permission_mode="acceptEdits"` 会自动批准文件操作
3. **依赖**: 需要本地安装 Python 及相关库
4. **清理**: 执行后的文件会保留在 `sandbox/` 目录中

## 自定义权限处理器

```python
async def safe_permission_handler(tool_name, input_data, context):
    # 阻止危险操作
    if tool_name == "Bash":
        command = input_data.get("command", "")
        if "rm -rf" in command:
            return {"behavior": "deny", "message": "Dangerous command blocked"}

    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(
    allowed_tools=["Bash", "Write"],
    can_use_tool=safe_permission_handler,
)
```
