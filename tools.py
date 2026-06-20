#!/usr/bin/env python3
"""
工具模块：read_pdf 和 summarize_text 两个 Skill 的实现
"""

import os
import json
from pypdf import PdfReader
from config import client, MODEL_NAME


# ============================================================
# TOOL 1: READ PDF
# ============================================================

def read_pdf(file_path: str) -> str:
    """
    读取 PDF 文件并提取全文文本。
    返回值：{"success": bool, "content": str, "error": str} 的 JSON 字符串
    """
    result = {"success": False, "content": "", "error": ""}
    
    try:
        if not os.path.exists(file_path):
            result["error"] = f"文件不存在: {file_path}"
            return json.dumps(result, ensure_ascii=False)
        
        if not file_path.lower().endswith(".pdf"):
            result["error"] = f"不是 PDF 文件: {file_path}"
            return json.dumps(result, ensure_ascii=False)
        
        reader = PdfReader(file_path)
        
        if reader.is_encrypted:
            result["error"] = "PDF 文件已加密，无法读取"
            return json.dumps(result, ensure_ascii=False)
        
        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"[第{page_num}页]\n{page_text}")
        
        if not text_parts:
            result["error"] = "PDF 中未提取到任何文本（可能为扫描件）"
            return json.dumps(result, ensure_ascii=False)
        
        result["success"] = True
        result["content"] = "\n\n".join(text_parts)
        return json.dumps(result, ensure_ascii=False)
    
    except Exception as e:
        result["error"] = f"读取 PDF 时发生异常: {str(e)}"
        return json.dumps(result, ensure_ascii=False)


# ============================================================
# TOOL 2: SUMMARIZE TEXT
# ============================================================

def summarize_text(text: str, max_length: int = 500) -> str:
    """
    调用 LLM 对文本生成结构化摘要。
    返回值：{"success": bool, "summary": str, "error": str} 的 JSON 字符串
    """
    result = {"success": False, "summary": "", "error": ""}
    
    try:
        if not text or len(text.strip()) < 10:
            result["error"] = "文本内容太短，无法生成有意义的摘要"
            return json.dumps(result, ensure_ascii=False)
        
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n... (文本过长，已截断)"
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个专业的文档摘要助手。请用中文生成高质量的结构化摘要。\n"
                        "输出格式：\n"
                        "1. 核心主题：一句话概括文档主题\n"
                        "2. 关键要点：3-5 个要点，用序号列出\n"
                        "3. 结论：一句话总结"
                    )
                },
                {
                    "role": "user",
                    "content": f"请为以下文档生成摘要（不超过 {max_length} 字）：\n\n{text}"
                }
            ],
            temperature=0.3,
            max_tokens=min(max_length * 2, 2048)
        )
        
        summary = response.choices[0].message.content
        if not summary:
            result["error"] = "LLM 返回了空摘要"
            return json.dumps(result, ensure_ascii=False)
        
        result["success"] = True
        result["summary"] = summary
        return json.dumps(result, ensure_ascii=False)
    
    except Exception as e:
        result["error"] = f"生成摘要时发生异常: {str(e)}"
        return json.dumps(result, ensure_ascii=False)


# ============================================================
# TOOL DISPATCHER
# ============================================================

def execute_tool(tool_name: str, arguments: dict) -> str:
    """根据工具名和参数分发给对应的工具函数。"""
    if tool_name == "read_pdf":
        return read_pdf(arguments["file_path"])
    elif tool_name == "summarize_text":
        # 防御性类型转换
        max_len = arguments.get("max_length", 500)
        if isinstance(max_len, str):
            max_len = int(max_len)
        return summarize_text(
            text=arguments["text"],
            max_length=max_len
        )
    else:
        return json.dumps({
            "success": False,
            "error": f"未知工具: {tool_name}"
        }, ensure_ascii=False)