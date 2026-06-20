#!/usr/bin/env python3
"""
CLI 模块：命令行交互界面
"""

from agent import agent_loop


def main():
    """命令行交互入口"""
    print("=" * 60)
    print("📄 PDF 摘要 Agent (BYOA Experiment)")
    print("🤖 模型: deepseek-chat")
    print("=" * 60)
    print("输入 PDF 文件路径，我将为你生成结构化摘要。")
    print("输入 'exit' 或 'quit' 退出。")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n📁 请输入 PDF 路径: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("exit", "quit", "q"):
                print("再见！")
                break
            
            print("\n⏳ Agent 正在处理，请稍候...\n")
            
            result = agent_loop(user_input)
            
            print("\n" + "=" * 60)
            print("📋 摘要结果:")
            print("=" * 60)
            print(result)
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生异常: {str(e)}")
            print("请检查 API Key 是否正确，网络是否通畅。")


if __name__ == "__main__":
    main()