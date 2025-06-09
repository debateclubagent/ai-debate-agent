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

# Prompt 构建函数
def build_yellow_prompt(question, previous_rounds, votes):
    ref = ""
    vote_summary = []
    for i in range(len(votes)//4):
        if votes.get(f"like_yellow_{i}"): vote_summary.append(f"你在第{i+1}轮支持了黄帽观点")
        if votes.get(f"dislike_yellow_{i}"): vote_summary.append(f"你在第{i+1}轮反对了黄帽观点")
    vote_hint = "
".join(vote_summary)
    if previous_rounds:
        last_black = previous_rounds[-1].get("black", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_black:
            ref = f"
请结合上轮黑帽的观点进行回应，特别是他指出的问题或误判：{last_black}"
    return f"""你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：**{question}**{ref}

{vote_hint}

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
}}"""你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：**{question}**{ref}

{vote_hint}

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
}}"""你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
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

def build_black_prompt(question, yellow_viewpoint, previous_rounds, votes):
    ref = ""
    vote_summary = []
    for i in range(len(votes)//4):
        if votes.get(f"like_black_{i}"): vote_summary.append(f"你在第{i+1}轮支持了黑帽观点")
        if votes.get(f"dislike_black_{i}"): vote_summary.append(f"你在第{i+1}轮反对了黑帽观点")
        if votes.get(f"like_yellow_{i}"): vote_summary.append(f"你在第{i+1}轮更倾向黄帽")
    vote_hint = "
".join(vote_summary)
    if previous_rounds:
        last_yellow = previous_rounds[-1].get("yellow", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_yellow:
            ref = f"
你还可以进一步回应上轮黄帽的新观点：{last_yellow}"
    return f"""你是“黑帽思维者”，你擅长理性地识别问题中的潜在风险、不可控因素、可能被忽略的限制。

用户的问题是：**{question}**

请你围绕“黄帽观点中提到的积极方向”进行反思，并展开辩论：
你必须引用黄帽的某个具体说法进行回应，例如：“黄帽提到...，但我认为...”
请确保回应清晰、有针对性，体现辩论感。

黄帽的观点是：“{yellow_viewpoint}”{ref}

{vote_hint}

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
}}"""你是“黑帽思维者”，你擅长理性地识别问题中的潜在风险、不可控因素、可能被忽略的限制。

用户的问题是：**{question}**

请你围绕“黄帽观点中提到的积极方向”进行反思，并展开辩论：
你必须引用黄帽的某个具体说法进行回应，例如：“黄帽提到...，但我认为...”
请确保回应清晰、有针对性，体现辩论感。

黄帽的观点是：“{yellow_viewpoint}”{ref}

{vote_hint}

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
}}"""你是“黑帽思维者”，你擅长理性地识别问题中的潜在风险、不可控因素、可能被忽略的限制。

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

def build_blue_prompt(question, yellow_viewpoint, black_viewpoint, votes):
    support_summary = []
    for i in range(len(votes)//4):
        if votes.get(f"like_yellow_{i}"): support_summary.append(f"第{i+1}轮用户支持黄帽")
        if votes.get(f"dislike_yellow_{i}"): support_summary.append(f"第{i+1}轮用户不支持黄帽")
        if votes.get(f"like_black_{i}"): support_summary.append(f"第{i+1}轮用户支持黑帽")
        if votes.get(f"dislike_black_{i}"): support_summary.append(f"第{i+1}轮用户不支持黑帽")
    vote_text = "\n".join(support_summary)

    return f"""你是“蓝帽思维者”，你的职责是整合前两者的观点，并帮助用户达成理性的判断。

用户的问题是：**{question}**

黄帽提出的观点是：“{yellow_viewpoint}”
黑帽提出的观点是：“{black_viewpoint}”

以下是用户在不同轮次中对观点的倾向：
{vote_text}

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

# 页面设置与初始化
st.set_page_config(page_title="六顶思考帽 · AI 辩论器", layout="wide")
st.title("🧠 六顶思考帽 · AI 辩论引导")

question = st.text_input("请输入你的问题：", placeholder="例如：我要不要离职")
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "votes" not in st.session_state:
    st.session_state.votes = {}
if "show_training" not in st.session_state:
    st.session_state.show_training = {}

# 生成新一轮观点按钮
if st.button("开始第一轮" if len(st.session_state.rounds) == 0 else "🔁 接着 Battle") and question:
    previous_rounds = st.session_state.rounds
    votes_snapshot = st.session_state.votes.copy()

    with st.spinner("黄帽思考中..."):
        yellow_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_yellow_prompt(question, previous_rounds, votes_snapshot)}],
            temperature=0.7
        ).choices[0].message.content
        yellow = safe_json_parse(yellow_raw, "黄帽")

    yellow_view = yellow['card_1']['content']['viewpoint']

    with st.spinner("黑帽反思中..."):
        black_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_black_prompt(question, yellow_view, previous_rounds, votes_snapshot)}],
            temperature=0.7
        ).choices[0].message.content
        black = safe_json_parse(black_raw, "黑帽")

    black_view = black['card_1']['content']['viewpoint']

    with st.spinner("蓝帽总结中..."):
        blue_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, yellow_view, black_view, votes_snapshot)}],
            temperature=0.7
        ).choices[0].message.content
        blue = safe_json_parse(blue_raw, "蓝帽")

    st.session_state.rounds.append({"yellow": yellow, "black": black, "blue": blue})
    st.rerun()

# 观点展示区（并排 + 点赞独立 + 思维训练）
for idx, round_data in enumerate(st.session_state.rounds):
    st.markdown(f"## 🎯 第{idx+1}轮观点对决")
    col1, col2, col3 = st.columns(3)
    for role, col in zip(["yellow", "black", "blue"], [col1, col2, col3]):
        with col:
            vote_like_key = f"like_{role}_{idx}"
            vote_dislike_key = f"dislike_{role}_{idx}"
            is_liked = st.session_state.votes.get(vote_like_key, False)
            is_disliked = st.session_state.votes.get(vote_dislike_key, False)

            card = round_data[role]
            card1 = card.get("card_1") or card.get("card")
            st.markdown(f"### {'🟡 黄帽' if role=='yellow' else '⚫ 黑帽' if role=='black' else '🔵 蓝帽'}")
            st.markdown(f"**{card1['title']}**")
            st.markdown(card1["content"].get("viewpoint") if isinstance(card1["content"], dict) else card1["content"])
            if isinstance(card1["content"], dict) and "evidence" in card1["content"]:
                st.markdown(card1["content"]["evidence"])

            if role in ["yellow", "black"] and card.get("card_2"):
                show_key = f"show_training_{role}_{idx}"
                if show_key not in st.session_state:
                    st.session_state[show_key] = False
                show_training = st.toggle("🧠 展开思维训练", key=show_key)
                if show_training:
                    card2 = card.get("card_2")
                    st.markdown(f"**{card2['title']}**")
                    st.markdown(card2["content"].get("thinking_path", ""))
                    st.markdown(card2["content"].get("training_tip", ""))

            cols = st.columns(2)
            with cols[0]:
                if st.button("👍 支持" + (" ✅" if is_liked else ""), key=vote_like_key):
                    st.session_state.votes[vote_like_key] = not is_liked
                    if not is_liked:
                        st.session_state.votes[vote_dislike_key] = False
            with cols[1]:
                if st.button("👎 不支持" + (" ✅" if is_disliked else ""), key=vote_dislike_key):
                    st.session_state.votes[vote_dislike_key] = not is_disliked
                    if not is_disliked:
                        st.session_state.votes[vote_like_key] = False

            if is_liked:
                st.success("你支持了这个观点")
            elif is_disliked:
                st.error("你不支持这个观点")

# 总结按钮逻辑
if st.button("🧾 总结观点") and st.session_state.rounds:
    last = st.session_state.rounds[-1]
    yellow_last = last["yellow"]["card_1"]["content"]["viewpoint"]
    black_last = last["black"]["card_1"]["content"]["viewpoint"]
    with st.spinner("蓝帽总结中..."):
        blue_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, yellow_last, black_last, st.session_state.votes)}],
            temperature=0.7
        ).choices[0].message.content
        blue = safe_json_parse(blue_raw, "蓝帽")
        st.markdown("### 🧠 蓝帽新总结")
        st.markdown(blue["card"]["content"])
        st.session_state.rounds[-1]["blue"] = blue
