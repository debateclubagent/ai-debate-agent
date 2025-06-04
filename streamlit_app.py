import streamlit as st
import requests

# 加载 secret token
HF_TOKEN = st.secrets["HF_TOKEN"]
API_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased-distilled-squad"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def query(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"出错啦！状态码：{response.status_code}，返回内容：{response.text}")
        return None

# Streamlit 页面
st.title("黄帽 Agent 🌞 在线问答")

question = st.text_input("你想问什么？", value="What is the benefit of free trials?")
context = st.text_area("提供背景信息（黄帽语气）", height=200, value="""
Offering a free trial helps users experience value before commitment. 
It lowers risk, builds trust, and encourages user engagement, especially for new users.
""")

if st.button("💬 获取黄帽回答"):
    with st.spinner("黄帽 Agent 思考中..."):
        output = query({
            "inputs": {
                "question": question,
                "context": context
            }
        })
        if output and isinstance(output, dict) and "answer" in output:
            st.success("🌟 回答：" + output["answer"])
