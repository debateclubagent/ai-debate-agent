import streamlit as st
import json
from openai import OpenAI

# 从 Streamlit secrets 读取 API Key
api_key = st.secrets["DEEPSEEK_API_KEY"]

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com/v1"
)

def build_prompt(question):
    return f"你是一个擅长发现问题中积极潜力的乐观助手。请分析以下问题的正向价值：{question}"

# Streamlit 页面结构
st.title("🟡 黄帽思维生成器")

question = st.text_area("请输入你的问题：", height=120)

if st.button("生成回答") and question:
    with st.spinner("正在生成，请稍候..."):
        try:
            prompt = build_prompt(question)

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个理性乐观的产品思维助理。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )

            reply = response.choices[0].message.content
            st.subheader("模型原始输出：")
            st.code(reply)

        except Exception as e:
            st.error("⚠️ 出错了，请查看异常信息：")
            st.exception(e)
