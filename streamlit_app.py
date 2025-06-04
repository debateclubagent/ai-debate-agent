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
    prompt = f"""
你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：{question}

请将你的回答封装为一个 JSON 对象，结构如下：

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

请你根据以下四段内容思考并生成 JSON 内容：

1. 🎯 我的观点：说出你对这个问题的积极判断，你认为它最可能带来什么好处，从哪个角度值得一试。
2. 📚 我的依据：解释你为何这样判断，引用你熟悉的事实、经验、研究、案例或趋势。
3. 🧠 我为什么会这样思考：说明黄帽惯常聚焦哪里，你是如何识别机会点的。
4. 🧩 你也可以这样练：教用户如何训练这种思考方式。

只输出结构规范的 JSON 对象本体。
"""
    return prompt

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
                    {"role": "system", "content": "你是一个理性乐观、结构清晰的黄帽思维助理，你的任务是将用户的问题输出为标准 JSON 格式。回答必须符合以下结构，并且只返回 JSON 本体，不要包含 Markdown、注释或额外解释。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )

            reply = response.choices[0].message.content

            # Debug：先展示完整原始返回内容
            st.subheader("🧾 模型原始输出")
            st.code(reply)

            # 尝试提取 JSON 对象（从第一个 { 开始）
            try:
                json_start = reply.find('{')
                json_str = reply[json_start:].split('```')[0].strip()
                data = json.loads(json_str)

                with st.container():
                    with st.container():
                        st.markdown(f"""
                        <details open>
                        <summary style='font-size: 20px; font-weight: bold;'>📂 问题的正向判断</summary>
                        <div style='padding-left: 1em; padding-top: 0.5em;'>
                        <p>{data['card_a']['content']['viewpoint']}</p>
                        <p>{data['card_a']['content']['evidence']}</p>
                        </div>
                        </details>
                        """, unsafe_allow_html=True)

                    with st.container():
                        st.markdown(f"""
                        <details open>
                        <summary style='font-size: 20px; font-weight: bold;'>📂 思维方式与训练建议</summary>
                        <div style='padding-left: 1em; padding-top: 0.5em;'>
                        <p>{data['card_b']['content']['thinking_path']}</p>
                        <p>{data['card_b']['content']['training_tip']}</p>
                        </div>
                        </details>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error("⚠️ 无法解析模型输出为 JSON，请检查返回格式。")
                st.exception(e)

        except Exception as e:
            st.error("⚠️ 出错了，请查看异常信息：")
            st.exception(e)
