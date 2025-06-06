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

请你围绕“黄帽观点中提到的积极方向”进行反思，并展开辩论：请引用黄帽的某个具体说法进行回应，例如“黄帽提到...，但我认为...”

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

# 👇👇👇 主程序入口逻辑

st.set_page_config(page_title="六顶思考帽观点生成器", layout="wide")
st.title("🎩 六顶思考帽：AI 观点生成器")

question = st.text_area("请输入你的问题：", placeholder="例如：我要不要离职")
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

def display_card(card):
    for k, v in card["content"].items():
        st.write(v)

if st.button("生成多角色观点") and question:
    with st.spinner("🟡 黄帽思考中..."):
        yellow_prompt = build_yellow_prompt(question, st.session_state.rounds)
        yellow_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": yellow_prompt}]
        )
        yellow_data = safe_json_parse(yellow_response.choices[0].message.content, "黄帽")

    if yellow_data:
        yellow_view = yellow_data.get("card_1", {}).get("content", {}).get("viewpoint", "")
        with st.spinner("⚫ 黑帽思考中..."):
            black_prompt = build_black_prompt(question, yellow_view, st.session_state.rounds)
            black_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": black_prompt}]
            )
            black_data = safe_json_parse(black_response.choices[0].message.content, "黑帽")

        if black_data:
            black_view = black_data.get("card_1", {}).get("content", {}).get("viewpoint", "")
            with st.spinner("🔵 蓝帽总结中..."):
                blue_prompt = build_blue_prompt(question, yellow_view, black_view)
                blue_response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": blue_prompt}]
                )
                blue_data = safe_json_parse(blue_response.choices[0].message.content, "蓝帽")

            st.session_state.rounds.append({
                "yellow": yellow_data,
                "black": black_data,
                "blue": blue_data
            })

# 展示内容
for i, r in enumerate(st.session_state.rounds):
    with st.container():
        st.markdown(f"### 🟡 第{i+1}轮 黄帽观点")
        for c in ["card_1", "card_2"]:
            if c in r["yellow"]:
                with st.expander(r["yellow"][c]["title"]):
                    display_card(r["yellow"][c])
        st.markdown(f"### ⚫ 第{i+1}轮 黑帽观点")
        for c in ["card_1", "card_2"]:
            if c in r["black"]:
                with st.expander(r["black"][c]["title"]):
                    display_card(r["black"][c])
        if r.get("blue"):
            st.markdown(f"### 🔵 第{i+1}轮 蓝帽总结")
            with st.expander(r["blue"]["card"]["title"]):
                st.write(r["blue"]["card"]["content"])
