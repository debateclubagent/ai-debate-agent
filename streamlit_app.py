import streamlit as st
import requests

# 🟡 Hugging Face token，建议写在 .streamlit/secrets.toml 里
HF_TOKEN = st.secrets["HF_TOKEN"]  # 在 secrets.toml 中写：hf_token = "hf_..."
API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# 🔁 调用模型接口
def query(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"❌ 出错啦！状态码：{response.status_code}\n返回内容：{response.text}")
        return None

# 🧠 Streamlit 页面
st.set_page_config(page_title="黄帽 Agent 问答", page_icon="🟡")
st.title("🟡 黄帽 Agent 问答机")
st.markdown("从正向角度思考问题，发现潜在价值 🌱")

# ✍️ 用户输入
question = st.text_input("你想问什么？", value="What is the benefit of free trials?")
context = st.text_area("提供背景信息（黄帽语气）", height=200, value="""
Offering a free trial helps users experience value before commitment.
It lowers risk, builds trust, and encourages user engagement, especially for new users.
""")

# 🚀 触发推理
if st.button("🎯 获取黄帽回答"):
    if question.strip() and context.strip():
        with st.spinner("黄帽 Agent 正在认真思考中..."):
            # 加入黄帽语气 prompt（Prompt Engineering）
            enhanced_question = "从积极角度思考：" + question
            enhanced_context = (
                "请站在黄帽角度（正向思考、发现价值）来理解这段内容：\n\n"
                + context
            )

            # 模型调用
            result = query({
                "inputs": {
                    "question": enhanced_question,
                    "context": enhanced_context
                }
            })

            # 💡 显示结果
            if result and isinstance(result, dict) and "answer" in result:
                st.success("🟡 黄帽Agent的回答：")
                st.write(result["answer"])
    else:
        st.warning("⚠️ 请完整输入问题和背景内容！")
