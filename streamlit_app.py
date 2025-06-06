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
def build_yellow_prompt(question, previous=None):
    ref = f"\n请结合上轮黑帽的观点进行回应：{previous}" if previous else ""
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

def build_black_prompt(question, yellow_viewpoint, previous=None):
    ref = f"\n你还可以进一步回应上轮黄帽的新观点：{previous}" if previous else ""
    return f"""你是“黑帽思维者”，你擅长理性地识别问题中的潜在风险、不可控因素、可能被忽略的限制。

用户的问题是：**{question}**

请你围绕“黄帽观点中提到的积极方向”进行反思，从以下角度进行思考：
- 其中可能隐藏的误判是什么？
- 在现实中可能遭遇的困难、阻力或代价是什么？
- 对黄帽的乐观是否需要设定前提？

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

# 主函数部分
st.set_page_config(page_title="六顶思考帽 AI", layout="wide")
st.title("🎩 六顶思考帽： AI 观点生成器")
question = st.text_area("请输入你的问题：", placeholder="例如：我该不该先免费提供产品？")

if 'rounds' not in st.session_state:
    st.session_state.rounds = []

if st.button("生成初始观点"):
    st.session_state.rounds = []
    yellow_prompt = build_yellow_prompt(question)
    yellow_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": yellow_prompt}]
    )
    yellow_json = safe_json_parse(yellow_response.choices[0].message.content, "黄帽")

    yellow_viewpoint = yellow_json['card_1']['content']['viewpoint']
    black_prompt = build_black_prompt(question, yellow_viewpoint)
    black_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": black_prompt}]
    )
    black_json = safe_json_parse(black_response.choices[0].message.content, "黑帽")

    st.session_state.rounds.append((yellow_json, black_json))

if st.session_state.rounds:
    col1, col2, col3 = st.columns(3)

    with col1:
        for i, (yellow, _) in enumerate(st.session_state.rounds):
            with st.expander(f"🟡 黄帽观点 {i+1}", expanded=i == len(st.session_state.rounds)-1):
                st.write(yellow['card_1']['content']['viewpoint'])
                st.write(yellow['card_1']['content']['evidence'])
            with st.expander(f"🟡 思维方式与建议 {i+1}", expanded=False):
                st.write(yellow['card_2']['content']['thinking_path'])
                st.write(yellow['card_2']['content']['training_tip'])

    with col2:
        for i, (_, black) in enumerate(st.session_state.rounds):
            with st.expander(f"⚫ 黑帽观点 {i+1}", expanded=i == len(st.session_state.rounds)-1):
                st.write(black['card_1']['content']['viewpoint'])
                st.write(black['card_1']['content']['evidence'])
            with st.expander(f"⚫ 思维方式与建议 {i+1}", expanded=False):
                st.write(black['card_2']['content']['thinking_path'])
                st.write(black['card_2']['content']['training_tip'])

    with col3:
        if st.button("🔁 接着 Battle"):
            latest_yellow = st.session_state.rounds[-1][0]['card_1']['content']['viewpoint']
            latest_black = st.session_state.rounds[-1][1]['card_1']['content']['viewpoint']
            yellow_prompt = build_yellow_prompt(question, previous=latest_black)
            yellow_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": yellow_prompt}]
            )
            yellow_json = safe_json_parse(yellow_response.choices[0].message.content, "黄帽")

            yellow_viewpoint = yellow_json['card_1']['content']['viewpoint']
            black_prompt = build_black_prompt(question, yellow_viewpoint, previous=latest_yellow)
            black_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": black_prompt}]
            )
            black_json = safe_json_parse(black_response.choices[0].message.content, "黑帽")
            st.session_state.rounds.append((yellow_json, black_json))

        if st.button("📘 总结观点"):
            final_yellow = st.session_state.rounds[-1][0]['card_1']['content']['viewpoint']
            final_black = st.session_state.rounds[-1][1]['card_1']['content']['viewpoint']
            blue_prompt = build_blue_prompt(question, final_yellow, final_black)
            blue_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": blue_prompt}]
            )
            blue_json = safe_json_parse(blue_response.choices[0].message.content, "蓝帽")
            if blue_json:
                with st.expander("🔵 蓝帽总结与判断", expanded=True):
                    st.markdown(f"**{blue_json['card']['title']}**")
                    st.write(blue_json['card']['content'])
