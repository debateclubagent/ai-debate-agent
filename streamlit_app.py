# app.py
import streamlit as st
import json

st.set_page_config(page_title="黄帽思维卡片", layout="wide")

st.title("🟡 黄帽思维练习器")

# 用户输入问题
user_input = st.text_area("请输入你的问题", height=100)

if st.button("生成思维卡片"):
    if not user_input:
        st.warning("请输入一个问题")
    else:
        # 这里你可以调用模型生成 JSON 输出，我们先用 mock 数据
        mock_output = {
            "card_a": {
                "title": "问题的正向判断",
                "content": {
                    "viewpoint": "🎯 我的观点：我认为应该对免费用户提供7天免费试用...",
                    "evidence": "📚 我的依据：根据心理学中的“禀赋效应”..."
                }
            },
            "card_b": {
                "title": "思维方式与训练建议",
                "content": {
                    "thinking_path": "🧠 我为什么会这样思考：作为黄帽思维者...",
                    "training_tip": "🧩 你也可以这样练：每当遇到一个决策问题..."
                }
            }
        }

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(mock_output["card_a"]["title"])
            st.markdown(mock_output["card_a"]["content"]["viewpoint"])
            st.markdown(mock_output["card_a"]["content"]["evidence"])

        with col2:
            st.subheader(mock_output["card_b"]["title"])
            st.markdown(mock_output["card_b"]["content"]["thinking_path"])
            st.markdown(mock_output["card_b"]["content"]["training_tip"])
