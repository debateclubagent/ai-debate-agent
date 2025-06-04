import streamlit as st
import json

st.set_page_config(page_title="黄帽思维练习器", layout="wide")

st.title("🟡 黄帽思维练习器")

# 用户输入问题
user_input = st.text_area("请输入你的问题", height=100, placeholder="例如：我们是否应该为工具类产品提供7天免费试用？")

# 生成按钮
if st.button("生成思维卡片"):
    if not user_input:
        st.warning("请先输入一个问题！")
    else:
        # 🔧 这里先用 mock 数据，后续可替换为 Hugging Face 模型调用
        mock_output = {
            "card_a": {
                "title": "问题的正向判断",
                "content": {
                    "viewpoint": "🎯 我的观点：我认为应该对免费用户提供7天免费试用。这最可能带来的好处是增加用户的初始参与度和产品体验深度，同时为潜在付费用户提供一个无风险的探索机会，从而提升转化率。",
                    "evidence": "📚 我的依据：根据心理学中的“禀赋效应”，用户一旦开始使用产品，更容易产生情感连接和依赖感。此外，像Spotify、Dropbox等成功案例表明，免费试用策略显著提高了用户的留存率和付费意愿。"
                }
            },
            "card_b": {
                "title": "思维方式与训练建议",
                "content": {
                    "thinking_path": "🧠 我为什么会这样思考：作为黄帽思维者，我关注的是如何通过低成本的尝试激发用户的潜在需求和兴趣。我形成这种思考习惯，来自于对用户行为模式的深入观察，以及多次验证小投入可以带来大回报的经验。",
                    "training_tip": "🧩 你也可以这样练：每当遇到一个决策问题，先问自己“这个方案最有可能激活哪些潜在机会”，然后列出这些机会的具体表现和可能带来的长期收益，这会帮助你培养对“机会点”的敏锐洞察力。"
                }
            }
        }

        # === 样式化渲染函数 ===
        def render_card(title, content_dict, bg_color="#f9f9f9"):
            card_html = f"""
            <div style="
                background-color: {bg_color};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.06);
                border: 1px solid #e0e0e0;
                height: 100%;
                font-size: 15px;
            ">
                <h3 style="margin-top: 0; margin-bottom: 12px;">{title}</h3>
                <p>{content_dict.get('viewpoint', '')}</p>
                <p>{content_dict.get('evidence', '')}</p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        def render_training_card(title, content_dict, bg_color="#f4f8ff"):
            card_html = f"""
            <div style="
                background-color: {bg_color};
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.06);
                border: 1px solid #dce3f0;
                height: 100%;
                font-size: 15px;
            ">
                <h3 style="margin-top: 0; margin-bottom: 12px;">{title}</h3>
                <p>{content_dict.get('thinking_path', '')}</p>
                <p>{content_dict.get('training_tip', '')}</p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            render_card(
                title=mock_output["card_a"]["title"],
                content_dict=mock_output["card_a"]["content"],
                bg_color="#fcfcfc"
            )

        with col2:
            render_training_card(
                title=mock_output["card_b"]["title"],
                content_dict=mock_output["card_b"]["content"],
                bg_color="#f0f7ff"
            )
