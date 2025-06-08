import streamlit as st
import json
from openai import OpenAI

# 从 Streamlit secrets 读取 API Key
api_key = st.secrets["DEEPSEEK_API_KEY"]

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# JSON 解析函数
def safe_json_parse(raw, label):
    if not raw or not raw.strip():
        st.warning(f"⚠️ {label} 输出为空。")
        return None
    if raw.strip().startswith("```json"):
        raw = raw.strip()[7:-3].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        st.error(f"⚠️ {label} 的输出不是合法 JSON：{e}")
        st.text_area("原始返回内容", raw, height=300)
        return None

# 三顶帽子 prompt 构建函数

def build_yellow_prompt(question, previous_rounds):
    ref = ""
    if previous_rounds:
        last_black = previous_rounds[-1].get("black", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_black:
            ref = f"\n请结合上轮黑帽的观点进行回应，特别是他指出的问题或误判：{last_black}"
    return f"""你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：**{question}**{ref}

请按以下结构输出，并确保是合法 JSON：

{{
  "card_1": {{
    "title": "问题的正向判断",
    "content": {{
      "viewpoint": "🎯 我的观点：...",
      "evidence": "📚 我的依据：..."
    }}
  }},
  "card_2": {{
    "title": "思维方式与训练建议",
    "content": {{
      "thinking_path": "🧠 我为什么会这样思考：...",
      "training_tip": "🧩 你也可以这样练：..."
    }}
  }}
}}"""

def build_black_prompt(question, yellow_viewpoint, previous_rounds):
    ref = ""
    if previous_rounds:
        last_yellow = previous_rounds[-1].get("yellow", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_yellow:
            ref = f"\n你还可以进一步回应上轮黄帽的新观点：{last_yellow}"
    return f"""你是“黑帽思维者”，你擅长理性地识别问题中的潜在风险、不可控因素、可能被忽略的限制。

用户的问题是：**{question}**

请你围绕“黄帽观点中提到的积极方向”进行反思，并展开辩论：
你必须引用黄帽的某个具体说法进行回应，例如：“黄帽提到...，但我认为...”
请确保回应清晰、有针对性，体现辩论感。

黄帽的观点是：“{yellow_viewpoint}”{ref}

请按以下结构输出，并确保是合法 JSON：

{{
  "card_1": {{
    "title": "潜在风险与现实限制",
    "content": {{
      "viewpoint": "💣 我的观点：...",
      "evidence": "📉 我的依据：..."
    }}
  }},
  "card_2": {{
    "title": "思维方式与训练建议",
    "content": {{
      "thinking_path": "🧠 我为什么会这样思考：...",
      "training_tip": "🧩 你也可以这样练：..."
    }}
  }}
}}"""

def build_blue_prompt(question, yellow_viewpoint, black_viewpoint):
    return f"""你是“蓝帽思维者”，你的职责是整合前两者的观点，并帮助用户达成理性的判断。

用户的问题是：**{question}**

黄帽提出的观点是：“{yellow_viewpoint}”
黑帽提出的观点是：“{black_viewpoint}”

请你基于以上内容，给出总结性判断，包括：
- 你如何看待两者的出发点？
- 你对该问题的整合性看法
- 如果是你，你会如何决策？理由是什么？

请输出以下结构的 JSON（不要加 ```、不要解释）：

{{
  "card": {{
    "title": "总结与判断",
    "content": "⚖️ 我的判断：..."
  }}
}}"""

# ✅ 主程序逻辑整合

st.set_page_config(page_title="六顶思考帽 · AI 辩论器", layout="wide")
st.title("🧠 六顶思考帽 · AI 辩论引导")

question = st.text_input("请输入你的问题：", placeholder="例如：我要不要离职")

if "rounds" not in st.session_state:
    st.session_state.rounds = []

if st.button("开始第一轮") and question:
    with st.spinner("黄帽思考中..."):
        yellow_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_yellow_prompt(question, st.session_state.rounds)}],
            temperature=0.7
        ).choices[0].message.content
        yellow = safe_json_parse(yellow_raw, "黄帽")

    with st.spinner("黑帽反思中..."):
        black_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_black_prompt(question, yellow['card_1']['content']['viewpoint'], st.session_state.rounds)}],
            temperature=0.7
        ).choices[0].message.content
        black = safe_json_parse(black_raw, "黑帽")

    with st.spinner("蓝帽总结中..."):
        blue_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, yellow['card_1']['content']['viewpoint'], black['card_1']['content']['viewpoint'])}],
            temperature=0.7
        ).choices[0].message.content
        blue = safe_json_parse(blue_raw, "蓝帽")

    st.session_state.rounds.append({"yellow": yellow, "black": black, "blue": blue})

# 展示最新一轮结果（如有）
if st.session_state.rounds:
    latest = st.session_state.rounds[-1]
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🟡 黄帽")
        st.markdown(latest["yellow"]["card_1"]["content"]["viewpoint"])
        st.markdown(latest["yellow"]["card_1"]["content"]["evidence"])
        with st.expander("🧠 思维训练"):
            st.markdown(latest["yellow"]["card_2"]["content"]["thinking_path"])
            st.markdown(latest["yellow"]["card_2"]["content"]["training_tip"])

    with col2:
        st.subheader("⚫ 黑帽")
        st.markdown(latest["black"]["card_1"]["content"]["viewpoint"])
        st.markdown(latest["black"]["card_1"]["content"]["evidence"])
        with st.expander("🧠 思维训练"):
            st.markdown(latest["black"]["card_2"]["content"]["thinking_path"])
            st.markdown(latest["black"]["card_2"]["content"]["training_tip"])

    with col3:
        st.subheader("🔵 蓝帽总结")
        st.markdown(latest["blue"]["card"]["content"])

    st.markdown("---")

    col_battle, col_summary = st.columns(2)
    with col_battle:
        if st.button("🔁 接着 Battle"):
            yellow_last = latest["yellow"]["card_1"]["content"]["viewpoint"]
            black_last = latest["black"]["card_1"]["content"]["viewpoint"]

            with st.spinner("黄帽思考中..."):
                yellow_raw = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": build_yellow_prompt(question, st.session_state.rounds)}],
                    temperature=0.7
                ).choices[0].message.content
                yellow = safe_json_parse(yellow_raw, "黄帽")

            with st.spinner("黑帽反思中..."):
                black_raw = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": build_black_prompt(question, yellow_last, st.session_state.rounds)}],
                    temperature=0.7
                ).choices[0].message.content
                black = safe_json_parse(black_raw, "黑帽")

            with st.spinner("蓝帽总结中..."):
                blue_raw = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": build_blue_prompt(question, yellow_last, black["card_1"]["content"]["viewpoint"])}],
                    temperature=0.7
                ).choices[0].message.content
                blue = safe_json_parse(blue_raw, "蓝帽")

            st.session_state.rounds.append({"yellow": yellow, "black": black, "blue": blue})

    with col_summary:
        if st.button("🧾 总结观点"):
            yellow_last = latest["yellow"]["card_1"]["content"]["viewpoint"]
            black_last = latest["black"]["card_1"]["content"]["viewpoint"]
            with st.spinner("蓝帽总结中..."):
                blue_raw = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": build_blue_prompt(question, yellow_last, black_last)}],
                    temperature=0.7
                ).choices[0].message.content
                blue = safe_json_parse(blue_raw, "蓝帽")
                st.markdown("### 🧠 蓝帽新总结")
                st.markdown(blue["card"]["content"])
