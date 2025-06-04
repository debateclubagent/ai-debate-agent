import streamlit as st
from transformers import pipeline

# 设置页面标题
st.set_page_config(page_title="黄帽思维卡片助手")
st.title("🟡 黄帽思维卡片生成器")

# 初始化生成模型（使用本地 gpt2）
@st.cache_resource
def load_model():
    return pipeline("text-generation", model="gpt2")

model = load_model()

# 用户输入问题
question = st.text_input("请输入你想探讨的问题：")

if question:
    with st.spinner("思考中，请稍候..."):
        prompt = (
            f"请作为一位拥有黄帽思维的AI助手，分析以下问题，并生成两个卡片内容，输出为标准JSON格式：\n"
            f"问题：{question}\n\n"
            f"要求输出格式如下：\n"
            f"{{\n"
            f"  \"card_a\": {{\n"
            f"    \"title\": \"问题的正向判断\",\n"
            f"    \"content\": {{\n"
            f"      \"viewpoint\": \"🎯 我的观点：...\",\n"
            f"      \"evidence\": \"📚 我的依据：...\"\n"
            f"    }}\n"
            f"  }},\n"
            f"  \"card_b\": {{\n"
            f"    \"title\": \"思维方式与训练建议\",\n"
            f"    \"content\": {{\n"
            f"      \"thinking_path\": \"🧠 我为什么会这样思考：...\",\n"
            f"      \"training_tip\": \"🧩 你也可以这样练：...\"\n"
            f"    }}\n"
            f"  }}\n"
            f"}}"
        )

        response = model(prompt, max_new_tokens=300, do_sample=True)[0]['generated_text']

        try:
            json_start = response.find("{")
            result = response[json_start:]
            parsed = json.loads(result)

            # 渲染卡片A
            with st.container():
                st.subheader(parsed['card_a']['title'])
                st.markdown(f"**观点**：{parsed['card_a']['content']['viewpoint']}")
                st.markdown(f"**依据**：{parsed['card_a']['content']['evidence']}")

            # 渲染卡片B
            with st.container():
                st.subheader(parsed['card_b']['title'])
                st.markdown(f"**思考路径**：{parsed['card_b']['content']['thinking_path']}")
                st.markdown(f"**训练建议**：{parsed['card_b']['content']['training_tip']}")

        except Exception as e:
            st.error("⚠️ 模型输出解析失败，请尝试重新输入或更换模型。")
            st.text_area("原始模型输出：", value=response, height=300)
