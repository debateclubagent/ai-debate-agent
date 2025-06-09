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

def build_blue_prompt(question, yellow_viewpoint, black_viewpoint, yellow_vote="neutral", black_vote="neutral"):
    vote_summary = {
        "like": "用户支持该观点 ✅",
        "dislike": "用户不支持该观点 ❌",
        "neutral": "用户未表达倾向"
    }

    return f"""你是“蓝帽思维者”，你的职责是整合前两者的观点，并帮助用户达成理性的判断。

用户的问题是：**{question}**

黄帽提出的观点是：“{yellow_viewpoint}”
→ {vote_summary.get(yellow_vote, '无')}。

黑帽提出的观点是：“{black_viewpoint}”
→ {vote_summary.get(black_vote, '无')}。

请你基于以上内容，做出以下三件事：
1. 综合黄帽与黑帽的出发点，指出它们在思维方式上的异同；
2. 根据用户的支持倾向，强化其认可方向，辅助其形成独立判断；
3. 给出你自己的建议或偏好（可以结合理性与情绪的平衡）。

请输出以下结构的 JSON（不要加 ```、不要解释）：

{{
  "card": {{
    "title": "总结与判断",
    "content": "⚖️ 我的判断：..."
  }}
}}"""

# ✅ 页面设置
st.set_page_config(page_title="六顶思考帽 · AI 辩论器", layout="wide")
st.title("🧠 六顶思考帽 · AI 辩论引导")

# ✅ 状态初始化
question = st.text_input("请输入你的问题：", placeholder="例如：我要不要离职")
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "votes" not in st.session_state:
    st.session_state.votes = {}

# ✅ 投票互斥逻辑
def handle_vote(role, idx, vote_type):
    other = "dislike" if vote_type == "like" else "like"
    st.session_state.votes[f"{role}_{idx}"] = vote_type
    st.session_state.votes.pop(f"{role}_{idx}_{other}", None)

# ✅ 卡片展示逻辑
def render_card(role, data, idx):
    with st.container():
        st.markdown(f"### {'🟡 黄帽视角' if role == 'yellow' else '⚫ 黑帽视角' if role == 'black' else '🔵 蓝帽总结'}")
        card = data.get("card_1") or data.get("card")
        st.markdown(f"**{card['title']}**")
        st.markdown(card["content"]["viewpoint"] if isinstance(card["content"], dict) else card["content"])
        if isinstance(card["content"], dict) and "evidence" in card["content"]:
            st.markdown(card["content"]["evidence"])

        if role in ["yellow", "black"]:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👍 支持", key=f"like_{role}_{idx}"):
                    handle_vote(role, idx, "like")
            with c2:
                if st.button("👎 反对", key=f"dislike_{role}_{idx}"):
                    handle_vote(role, idx, "dislike")

            # 思维训练
            if st.toggle("🧠 展开思维训练", key=f"train_{role}_{idx}"):
                st.markdown(data["card_2"]["content"]["thinking_path"])
                st.markdown(data["card_2"]["content"]["training_tip"])

# ✅ 轮次展示
for i, r in enumerate(st.session_state.rounds):
    st.markdown(f"## 🎯 第{i+1}轮对话")
    col1, col2, col3 = st.columns(3)
    with col1: render_card("yellow", r["yellow"], i)
    with col2: render_card("black", r["black"], i)
    with col3: render_card("blue", r["blue"], i)

# ✅ 开始 / 下一轮
if st.button("开始第一轮" if len(st.session_state.rounds) == 0 else "🔁 接着 Battle") and question:
    prev = st.session_state.rounds
    yellow_vote = st.session_state.votes.get(f"yellow_{len(prev)-1}", "neutral") if prev else "neutral"
    black_vote = st.session_state.votes.get(f"black_{len(prev)-1}", "neutral") if prev else "neutral"

    yellow_input = "" if yellow_vote != "like" and prev else None
    with st.spinner("黄帽生成中..."):
        y_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_yellow_prompt(question, prev)}],
            temperature=0.7
        ).choices[0].message.content
        yellow = safe_json_parse(y_raw, "黄帽")

    yellow_view = yellow['card_1']['content']['viewpoint'] if yellow_vote == "like" or not prev else ""
    with st.spinner("黑帽生成中..."):
        b_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_black_prompt(question, yellow_view, prev)}],
            temperature=0.7
        ).choices[0].message.content
        black = safe_json_parse(b_raw, "黑帽")

    black_view = black['card_1']['content']['viewpoint'] if black_vote == "like" or not prev else ""
    with st.spinner("蓝帽总结中..."):
        blue_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, yellow_view, black_view, yellow_vote, black_vote)}],
            temperature=0.7
        ).choices[0].message.content
        blue = safe_json_parse(blue_raw, "蓝帽")

    st.session_state.rounds.append({"yellow": yellow, "black": black, "blue": blue})
    st.rerun()

# ✅ 最终总结按钮
if st.button("🧾 总结所有观点") and st.session_state.rounds:
    last = st.session_state.rounds[-1]
    y_view = last["yellow"]["card_1"]["content"]["viewpoint"]
    b_view = last["black"]["card_1"]["content"]["viewpoint"]
    y_vote = st.session_state.votes.get(f"yellow_{len(st.session_state.rounds)-1}", "neutral")
    b_vote = st.session_state.votes.get(f"black_{len(st.session_state.rounds)-1}", "neutral")
    with st.spinner("蓝帽总结中..."):
        summary_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, y_view, b_view, y_vote, b_vote)}],
            temperature=0.7
        ).choices[0].message.content
        summary = safe_json_parse(summary_raw, "最终蓝帽")
        st.markdown("### 🔷 最终蓝帽总结")
        st.markdown(summary["card"]["content"])
