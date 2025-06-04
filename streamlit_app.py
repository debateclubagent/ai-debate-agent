import streamlit as st
import requests
import json

# 设置页面标题
st.set_page_config(page_title="问答助手")
st.title("🧠 问答生成器")

# 使用 Streamlit secrets 读取 Hugging Face Token
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
headers = {
    "Authorization": f"Bearer {st.secrets['HF_TOKEN']}"
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# 用户输入问题
question = st.text_input("请输入你的问题：")

if question:
    with st.spinner("正在调用 Hugging Face 模型生成回答..."):
        prompt = f"问题：{question}\n请简洁地用中文回答这个问题："
        output = query({
            "inputs": prompt,
            "options": {"wait_for_model": True}
        })

        if isinstance(output, list) and 'generated_text' in output[0]:
            st.subheader("模型回答")
            st.write(output[0]['generated_text'].replace(prompt, "").strip())
        else:
            st.error("❌ 模型没有返回有效的结果。请稍后再试或更换模型。")
