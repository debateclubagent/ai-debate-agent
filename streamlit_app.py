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

# 统一的 JSON 解析保护函数
def safe_json_parse(raw, label):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        st.error(f"⚠️ {label} 的输出不是合法 JSON：{e}")
        st.text_area("原始返回内容", raw, height=300)
        return None

# 黄帽 Prompt

def build_yellow_prompt(question):
    return f"""
你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：{question}

请按以下四段进行回答：

### 🎯 1. 【我的观点】
请说出你对这个问题的积极判断。
你认为它最可能带来什么好处？你会从哪个角度看它“值得一试”？

### 📚 2. 【我的依据】
说明你为什么会这样判断。
你参考了哪些事实、常识、用户行为、案例或趋势？
重点在于：让人看懂你是“理性乐观”，不是瞎乐观。

### 🧠 3. 【我为什么会这样思考】
请从黄帽的视角解释你是如何找到这个“积极角度”的。
你可以说明：
- 黄帽通常关注什么（被低估的价值点？能激发正反馈的机制？用户感知入口？）
- 在这个问题里，你是怎么识别到“值得从希望切入”的机会点的？
- 这反映了黄帽惯常的什么思维方式？

### 🧩 4. 【你也可以这样练】
请提供一个简洁、有指向性的练习建议，帮助用户像黄帽一样思考：
- 如何识别一个“值得轻试”的积极入口？
- 如何在困难中刻意寻找“有转机的部分”？
- 如何从局部希望点出发，引导出一个判断过程？
重点在于：不是套模板，而是训练“看到希望值不值试”的能力。

请将你的回答封装为 JSON 对象，结构如下：
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
注意：请严格按照 JSON 格式输出，不要加解释、引言或 Markdown。
"""

# 主函数
st.title("🎩 六顶思考帽：AI 观点生成器")
question = st.text_area("请输入你的问题：", placeholder="例如：我该不该先免费提供产品？")

if st.button("生成多角色观点"):
    if not question:
        st.warning("请输入一个问题！")
        st.stop()

    with st.spinner("🟡 黄帽思考中..."):
        yellow_prompt = build_yellow_prompt(question)
        yellow_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": yellow_prompt}
            ]
        )
        yellow_json = safe_json_parse(yellow_response.choices[0].message.content, "黄帽")
        if yellow_json is None:
            st.stop()

        with st.expander("🟡 黄帽视角：乐观可能"):
            st.markdown(f"**{yellow_json['card_a']['title']}**")
            st.write(yellow_json['card_a']['content']['viewpoint'])
            st.write(yellow_json['card_a']['content']['evidence'])
            st.markdown(f"**{yellow_json['card_b']['title']}**")
            st.write(yellow_json['card_b']['content']['thinking_path'])
            st.write(yellow_json['card_b']['content']['training_tip'])
