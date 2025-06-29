import streamlit as st
import json
from openai import OpenAI

api_key = st.secrets["DEEPSEEK_API_KEY"]
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")


def safe_json_parse(raw: str, label: str):
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


def build_yellow_prompt(question: str) -> str:
    return f"""你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：**{question}**

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


def build_black_prompt(question: str, yellow_viewpoint: str) -> str:
    return f"""你是“黑帽思维者”，你擅长理性地识别问题中的潜在风险、不可控因素、可能被忽略的限制。

用户的问题是：**{question}**

请你针对“黄帽观点中提到的积极方向”进行辩证反思，从以下角度展开：
- 黄帽提到的好处是否存在不切实际或过度乐观的成分？
- 其中是否隐藏风险、误判，或需要额外的条件才可能成立？
- 请用事实、数据或经验佐证你的判断。

黄帽的观点是：“{yellow_viewpoint}”

请按以下结构输出，并确保是合法 JSON：
{{
  "card_1": {{
    "title": "潜在风险与现实限制",
    "content": {{
      "viewpoint": "💣 我的观点：...（请引用黄帽内容并做出辩证回应）",
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


def build_blue_prompt(question: str, yellow_viewpoint: str, black_viewpoint: str) -> str:
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


def generate_hat_cards(question: str):
    yellow_prompt = build_yellow_prompt(question)
    yellow_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": yellow_prompt}]
    )
    yellow_json = safe_json_parse(yellow_response.choices[0].message.content, "黄帽")
    if not yellow_json:
        return None

    yellow_viewpoint = yellow_json['card_1']['content']['viewpoint']
    black_prompt = build_black_prompt(question, yellow_viewpoint)
    black_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": black_prompt}]
    )
    black_json = safe_json_parse(black_response.choices[0].message.content, "黑帽")
    if not black_json:
        return None

    black_viewpoint = black_json['card_1']['content']['viewpoint']
    blue_prompt = build_blue_prompt(question, yellow_viewpoint, black_viewpoint)
    blue_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": blue_prompt}]
    )
    blue_json = safe_json_parse(blue_response.choices[0].message.content, "蓝帽")
    if not blue_json:
        return None

    return {
        "yellow": yellow_json,
        "black": black_json,
        "blue": blue_json,
    }


st.set_page_config(page_title="AI 白板工具", layout="wide")
st.title("📝 白板思考工具")

if "cards" not in st.session_state:
    st.session_state.cards = []

question = st.text_area("输入你的问题：", placeholder="例如：我该不该先免费提供产品？")
if st.button("生成卡片"):
    if not question:
        st.warning("请输入一个问题！")
    else:
        with st.spinner("思考中..."):
            result = generate_hat_cards(question)
            if result:
                st.session_state.cards.append({"question": question, **result})

for idx, data in enumerate(st.session_state.cards, 1):
    st.markdown(f"### 问题 {idx}: {data['question']}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🟡 黄帽")
        st.write(data['yellow']['card_1']['content']['viewpoint'])
        st.write(data['yellow']['card_1']['content']['evidence'])
    with col2:
        st.markdown("#### ⚫ 黑帽")
        st.write(data['black']['card_1']['content']['viewpoint'])
        st.write(data['black']['card_1']['content']['evidence'])
    with col3:
        st.markdown("#### 🔵 蓝帽")
        st.markdown(f"**{data['blue']['card']['title']}**")
        st.write(data['blue']['card']['content'])
    st.divider()
