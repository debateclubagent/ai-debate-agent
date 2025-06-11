import streamlit as st
import json
from openai import OpenAI

# ✅ 必须第一句：设置页面配置
st.set_page_config(page_title="Six Thinking Hats · AI Debate", layout="wide")

# ✅ 初始语言状态（不能用 selectbox 直接赋值）
if "lang" not in st.session_state:
    st.session_state.lang = "English"

# ✅ 语言切换控件
lang = st.selectbox("🌐 Language / 语言", options=["English", "中文"], index=0 if st.session_state.lang == "English" else 1)
st.session_state.lang = lang

# ✅ 文本字典
T = {
    "title": {"English": "🧠 Six Thinking Hats · AI Debate Guide", "中文": "🧠 六顶思考帽 · AI 辩论引导"},
    "question_input": {"English": "Enter your question:", "中文": "请输入你的问题："},
    "question_ph": {"English": "e.g., Should I quit my job?", "中文": "例如：我要不要离职"},
    "start": {"English": "Start First Round", "中文": "开始第一轮"},
    "continue": {"English": "🔁 Continue Battle", "中文": "🔁 接着 Battle"},
    "round_title": {"English": "Round", "中文": "第"},
    "summarize": {"English": "🧾 Summarize All Viewpoints", "中文": "🧾 总结所有观点"},
    "final_summary": {"English": "🔷 Final Blue Hat Summary", "中文": "🔷 最终蓝帽总结"},
    "support": {"English": "👍 Support", "中文": "👍 支持"},
    "oppose": {"English": "👎 Oppose", "中文": "👎 反对"},
    "voted_support": {"English": "✅ Supported", "中文": "✅ 已支持"},
    "voted_oppose": {"English": "❌ Opposed", "中文": "❌ 已反对"},
    "thinking_train": {"English": "🧠 Expand Thinking Practice", "中文": "🧠 展开思维训练"},
}

st.title(T["title"][lang])
question = st.text_input(T["question_input"][lang], placeholder=T["question_ph"][lang])

# ✅ 初始化状态
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "votes" not in st.session_state:
    st.session_state.votes = {}
if "final_summary" not in st.session_state:
    st.session_state.final_summary = None

# ✅ 初始化 OpenAI
api_key = st.secrets["DEEPSEEK_API_KEY"]
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# ✅ JSON 安全解析
def safe_json_parse(raw, label):
    if not raw or not raw.strip():
        st.warning(f"⚠️ {label} output is empty.")
        return None
    if raw.strip().startswith("```json"):
        raw = raw.strip()[7:-3].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        st.error(f"⚠️ {label} output is not valid JSON: {e}")
        st.text_area("Raw response", raw, height=300)
        return None

# ✅ Prompt 构建函数
def build_yellow_prompt(q, prev):
    ref = ""
    if prev:
        last_black = prev[-1].get("black", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_black:
            ref = f"\nPlease respond to the last black hat's point: {last_black}"
    return f"""You are the Yellow Hat Thinker. Be optimistic and find opportunities.

Question: {q}{ref}

Return valid JSON:

{{
  "card_1": {{
    "title": "Positive Evaluation",
    "content": {{
      "viewpoint": "🎯 My Viewpoint: ...",
      "evidence": "📚 My Evidence: ..."
    }}
  }},
  "card_2": {{
    "title": "Thinking Path & Training",
    "content": {{
      "thinking_path": "🧠 Why I think this way: ...",
      "training_tip": "🧩 How you can train: ..."
    }}
  }}
}}"""

def build_black_prompt(q, yellow_viewpoint, prev):
    ref = ""
    if prev:
        last_yellow = prev[-1].get("yellow", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_yellow:
            ref = f"\nYou can also reflect on this Yellow Hat opinion: {last_yellow}"
    return f"""You are the Black Hat Thinker. Spot risks and downsides.

Question: {q}

Yellow Hat said: {yellow_viewpoint}{ref}

Return valid JSON:

{{
  "card_1": {{
    "title": "Risks & Limitations",
    "content": {{
      "viewpoint": "💣 My Viewpoint: ...",
      "evidence": "📉 My Evidence: ..."
    }}
  }},
  "card_2": {{
    "title": "Thinking Path & Training",
    "content": {{
      "thinking_path": "🧠 Why I think this way: ...",
      "training_tip": "🧩 How you can train: ..."
    }}
  }}
}}"""

def build_blue_prompt(q, yellow_v, black_v, y_vote, b_vote):
    vote_map = {
        "like": "User supports ✅",
        "dislike": "User disagrees ❌",
        "neutral": "User neutral"
    }
    return f"""You are the Blue Hat Thinker. Your task: summarize and guide.

Question: {q}

Yellow: {yellow_v} → {vote_map.get(y_vote, 'Unknown')}
Black: {black_v} → {vote_map.get(b_vote, 'Unknown')}

Return this JSON:

{{
  "card": {{
    "title": "Summary & Judgment",
    "content": "⚖️ My conclusion: ..."
  }}
}}"""

# ✅ 投票逻辑
def handle_vote(role, idx, vote_type):
    other = "dislike" if vote_type == "like" else "like"
    st.session_state.votes[f"{role}_{idx}"] = vote_type
    st.session_state.votes.pop(f"{role}_{idx}_{other}", None)

# ✅ 卡片渲染
def render_card(role, data, idx):
    role_label = {"yellow": "🟡 Yellow Hat", "black": "⚫ Black Hat"}
    st.markdown(f"### {role_label[role]}")
    card = data.get("card_1")
    st.markdown(f"**{card['title']}**")
    st.markdown(card["content"]["viewpoint"])
    if "evidence" in card["content"]:
        st.markdown(card["content"]["evidence"])

    vote_status = st.session_state.votes.get(f"{role}_{idx}", "neutral")
    c1, c2 = st.columns(2)
    with c1:
        label = T["voted_support"][lang] if vote_status == "like" else T["support"][lang]
        if st.button(label, key=f"like_{role}_{idx}"):
            handle_vote(role, idx, "like")
    with c2:
        label = T["voted_oppose"][lang] if vote_status == "dislike" else T["oppose"][lang]
        if st.button(label, key=f"dislike_{role}_{idx}"):
            handle_vote(role, idx, "dislike")

    if st.toggle(T["thinking_train"][lang], key=f"train_{role}_{idx}"):
        st.markdown(data["card_2"]["content"]["thinking_path"])
        st.markdown(data["card_2"]["content"]["training_tip"])

# ✅ 展示历史轮次
for i, r in enumerate(st.session_state.rounds):
    st.markdown(f"## 🎯 {T['round_title'][lang]} {i+1}")
    col1, col2 = st.columns(2)
    with col1: render_card("yellow", r["yellow"], i)
    with col2: render_card("black", r["black"], i)

# ✅ 开始新一轮
if st.button(T["start"][lang] if not st.session_state.rounds else T["continue"][lang]) and question:
    prev = st.session_state.rounds
    yellow_vote = st.session_state.votes.get(f"yellow_{len(prev)-1}", "neutral") if prev else "neutral"
    black_vote = st.session_state.votes.get(f"black_{len(prev)-1}", "neutral") if prev else "neutral"

    yellow_view = "" if yellow_vote != "like" and prev else None
    with st.spinner("Generating Yellow Hat..."):
        y_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_yellow_prompt(question, prev)}],
            temperature=0.7
        ).choices[0].message.content
        yellow = safe_json_parse(y_raw, "Yellow Hat")

    yellow_view = yellow['card_1']['content']['viewpoint']
    with st.spinner("Generating Black Hat..."):
        b_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_black_prompt(question, yellow_view, prev)}],
            temperature=0.7
        ).choices[0].message.content
        black = safe_json_parse(b_raw, "Black Hat")

    st.session_state.rounds.append({"yellow": yellow, "black": black})
    st.rerun()

# ✅ 蓝帽最终总结
if st.button(T["summarize"][lang]) and st.session_state.rounds:
    if not st.session_state.final_summary:
        last = st.session_state.rounds[-1]
        y_view = last["yellow"]["card_1"]["content"]["viewpoint"]
        b_view = last["black"]["card_1"]["content"]["viewpoint"]
        y_vote = st.session_state.votes.get(f"yellow_{len(st.session_state.rounds)-1}", "neutral")
        b_vote = st.session_state.votes.get(f"black_{len(st.session_state.rounds)-1}", "neutral")

        with st.spinner("Generating Blue Hat Summary..."):
            blue_raw = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": build_blue_prompt(question, y_view, b_view, y_vote, b_vote)}],
                temperature=0.7
            ).choices[0].message.content
            summary = safe_json_parse(blue_raw, "Blue Hat")
            st.session_state.final_summary = summary["card"]["content"]

    st.markdown(f"### {T['final_summary'][lang]}")
    st.markdown(st.session_state.final_summary)
