import streamlit as st
import json
import requests

# ✅ 安全读取 Hugging Face Token
HF_API_TOKEN = st.secrets["HF_TOKEN"]
HF_MODEL_ID = "HuggingFaceH4/zephyr-7b-alpha"  # 可更换其他 instruct 模型

st.set_page_config(page_title="黄帽思维练习器", layout="wide")
st.title("🟡 黄帽思维练习器")

# ===== 用户输入 =====
user_input = st.text_area("请输入你的问题", height=100, placeholder="例如：我们是否应该为工具类产品提供7天免费试用？")

# ===== 卡片样式函数 =====
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

def render_training_card(title, content_dict, bg_color="#f0f7ff"):
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

# ===== 模型请求函数 =====
def generate_json_from_huggingface(user_question):
    prompt = f"""
你是一个善于用黄帽思维判断问题的专家，请根据以下结构化格式来分析这个问题：

问题是：“{user_question}”

请输出 JSON 格式如下：
{{
  "card_a": {{
    "title": "问题的正向判断",
    "content": {{
      "viewpoint": "🎯 我的观点：...",
      "evidence": "📚 我的依据：..."
    }}
  }},
  "card_b": {{
    "title": "思维方式与训练建议",
    "content": {{
      "thinking_path": "🧠 我为什么会这样思考：...",
      "training_tip": "🧩 你也可以这样练：..."
    }}
  }}
}}
"""

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    response = requests.post(
        url=f"https://api-inference.huggingface.co/models/{HF_MODEL_ID}",
        headers=headers,
        json={"inputs": prompt}
    )

    result = response.json()
    if isinstance(result, list) and "generated_text" in result[0]:
        raw_output = result[0]["generated_text"]
    else:
        raw_output = result.get("generated_text", "")

    try:
        json_start = raw_output.find("{")
        json_data = json.loads(raw_output[json_start:])
        return json_data
    except Exception as e:
        return {"error": f"模型输出无法解析：{str(e)}", "raw": raw_output}

# ===== 触发逻辑 =====
if st.button("生成思维卡片"):
    if not user_input:
        st.warning("请先输入一个问题！")
    else:
        st.markdown("---")
        with st.spinner("正在生成中，请稍候..."):
            result = generate_json_from_huggingface(user_input)

        if "error" in result:
            st.error(result["error"])
            with st.expander("查看模型原始输出"):
                st.code(result["raw"])
        else:
            col1, col2 = st.columns(2)
            with col1:
                render_card(result["card_a"]["title"], result["card_a"]["content"])
            with col2:
                render_training_card(result["card_b"]["title"], result["card_b"]["content"])
