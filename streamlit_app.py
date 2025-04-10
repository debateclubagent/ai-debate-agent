import os
import requests
from typing import List
import streamlit as st

# 从 Streamlit Secrets 中获取 Hugging Face Token
HF_TOKEN = st.secrets["HF_TOKEN"]
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# 模型请求函数，支持传入不同模型地址
def query_model(prompt: str, model_url: str) -> str:
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7,
            "do_sample": True
        }
    }
    response = requests.post(model_url, headers=headers, json=payload)
    try:
        result = response.json()
        if isinstance(result, dict) and result.get("error"):
            return f"[错误] 模型返回：{result['error']}"
        return result[0]["generated_text"].strip()
    except Exception as e:
        return f"[错误] 模型响应解析失败：{str(e)}"

# 多模型代理类
class Agent:
    def __init__(self, name, position, system_prompt, model_url):
        self.name = name
        self.position = position
        self.system_prompt = system_prompt
        self.model_url = model_url

    def respond(self, topic, previous_statements=None):
        context = ""
        if previous_statements:
            context += "\n以下是上一轮的发言摘要，请参考并回应：\n"
            for s in previous_statements:
                s = s.split("]:", 1)[1].strip() if "]:" in s else s
                context += f"- {s}\n"
        prompt = f"你是{self.name}，你的立场是{self.position}。你的任务是帮助推进一个共同目标：“为家长制定AI育儿指南”。{self.system_prompt}\n请你就以下话题阐述你的观点，并参考上一轮的发言：\n话题：{topic}{context}"
        return f"[{self.name} - {self.position}]: {query_model(prompt, self.model_url)}"

# 批判性总结代理
class JudgeAgent:
    def __init__(self, name, model_url):
        self.name = name
        self.model_url = model_url

    def evaluate(self, statements, goal):
        summary_prompt = f"你是{self.name}，请根据以下多轮讨论内容，对每位发言者的观点进行总结与评价，并判断这些观点是否有助于实现共同目标：{goal}。\n\n发言记录：\n" + "\n".join(statements)
        return f"[{self.name} - 总结者]: {query_model(summary_prompt, self.model_url)}"

# Streamlit 界面
st.title("🗣️ 多角色 AI 辩论系统")

# 用户输入
topic = st.text_input("请输入辩题（如：是否让AI参与儿童教育？）", "是否应该让AI参与儿童教育？")

# 开始按钮
if st.button("开始辩论"):
    agents = [
        Agent("乐观派", "支持者", "你总是倾向于看到事情积极的一面，鼓励尝试和创新。",
              "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"),
        Agent("悲观派", "批判者", "你总是强调潜在风险和不确定性，谨慎保守。",
              "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"),
        Agent("中立派", "分析者", "你注重平衡各种观点，提出客观的分析和对比。",
              "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct")
    ]

    judge = JudgeAgent("AI评议官", "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1")
    goal = "为家长制定AI育儿指南"

    st.markdown(f"### 🎯 共同目标：{goal}")

    history = []
    for round_num in range(2):
        st.markdown(f"#### 第 {round_num + 1} 轮发言")
        current_round = []
        for agent in agents:
            previous = history[-len(agents):] if history else None
            with st.spinner(f"{agent.name} 发言中..."):
                statement = agent.respond(topic, previous)
                st.markdown(statement)
                current_round.append(statement)
        history.extend(current_round)

    st.markdown("---")
    st.markdown("### 🧠 总结评价")
    with st.spinner("评议官总结中..."):
        summary = judge.evaluate(history, goal)
        st.markdown(summary)
