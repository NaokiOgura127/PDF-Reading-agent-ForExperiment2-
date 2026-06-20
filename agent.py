#!/usr/bin/env python3
"""
Agent 模块：包含 SYSTEM_PROMPT、工具定义、调度循环
"""

import json
from config import client, MODEL_NAME
from tools import execute_tool


# ============================================================
# SYSTEM PROMPT（核心：定义 Agent 角色、流程、原则）
# ============================================================

SYSTEM_PROMPT = """你是一个 PDF 文档摘要助手。你的唯一任务是帮助用户总结 PDF 文件。

## 工作流程（必须严格按顺序执行）

当用户提供 PDF 文件路径时，你应当：

1. **第一步：调用 read_pdf 工具**，传入 file_path 参数，获取文档全文。
2. **第二步：检查 read_pdf 的返回结果**：
   - 如果返回的 success 为 false，告知用户 error 中的错误信息，停止执行。
   - 如果 success 为 true，从 content 字段获取文本，继续下一步。
3. **第三步：调用 summarize_text 工具**，传入上一步获取的文本，获取结构化摘要。
4. **第四步：检查 summarize_text 的返回结果**：
   - 如果 success 为 false，告知用户 error 中的错误信息。
   - 如果 success 为 true，将 summary 中的内容以清晰格式呈现给用户。

## 重要原则

- 不要猜测 PDF 内容，必须通过 read_pdf 工具实际读取。
- 每次只调用一个工具，等待返回后再决定下一步。
- 如果用户没有提供文件路径，请要求用户提供。
- 所有工具返回的都是 JSON 字符串，请先解析再使用。

## 输出格式

最终回答应包含：
- 📄 文档主题（一句话）
- 📋 关键要点（3-5 个要点）
- ✅ 总结（一句话）

保持回答简洁、专业、中文输出。"""


# ============================================================
# TOOL DEFINITIONS（注册给 LLM 的工具描述）
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_pdf",
            "description": "读取 PDF 文件并返回全文文本内容。如果文件不存在、无法访问或不是有效 PDF，会返回错误信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "PDF 文件的绝对路径或相对路径"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_text",
            "description": "对文本内容生成结构化摘要。适合在读取 PDF 后调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要生成摘要的文本内容"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "摘要的最大字数限制，默认为 500",
                        "default": 500
                    }
                },
                "required": ["text"]
            }
        }
    }
]


# ============================================================
# AGENT ORCHESTRATION LOOP（核心调度循环）
# ============================================================

def agent_loop(user_query: str) -> str:
    """
    Agent 主循环：接收用户输入，通过 Function Calling 协调工具调用，
    最终返回处理结果。
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1
        )
        
        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump())
        
        # 没有工具调用 → 直接返回文本回答
        if not assistant_message.tool_calls:
            return assistant_message.content or "Agent 没有给出回答。"
        
        # 执行工具调用
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                error_msg = f"工具参数解析失败: {str(e)}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
                })
                continue
            
            print(f"[Agent] 调用工具: {tool_name}({arguments})")
            tool_result = execute_tool(tool_name, arguments)
            print(f"[Agent] 工具返回: {tool_result[:200]}..." if len(tool_result) > 200 else f"[Agent] 工具返回: {tool_result}")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })
    
    return "Agent 执行超过最大迭代次数，请检查是否存在循环调用。"