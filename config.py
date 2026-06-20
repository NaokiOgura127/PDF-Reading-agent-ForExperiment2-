#!/usr/bin/env python3
"""
配置模块:API Key、模型、客户端初始化
"""

import os
from openai import OpenAI

# ============================================================
# 配置区（请在此填入你的 API Key）
# ============================================================

DEEPSEEK_API_KEY = "your_api_key"
MODEL_NAME = "deepseek-chat"  # 或 "deepseek-reasoner"

# ============================================================
# 客户端初始化
# ============================================================

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)