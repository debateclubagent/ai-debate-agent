import streamlit as st
import json
from openai import OpenAI

# Initialize
api_key = st.secrets["DEEPSEEK_API_KEY"]
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Language switch
lang = st.selectbox("🌐 Language / 语言", options=["English", "中文"], index=0)

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

# State
st.set_page_config(page_title=T["title"][lang], layout="wide")
st.title(T["title"][lang])
question = st.text_input(T["question_input"][lang], placeholder=T["question_ph"][lang])
if "rounds" not in st.session_state: st.session_state.rounds = []
if "votes" not in st.session_state: st.session_state.votes = {}
if "final_summary" not in st.session_state: st.session_state.final_summary = None

# Prompt builders (仅保留英文版本，简洁清晰，必要可扩中译版本)
def build_yellow_prompt(q, prev): ...
def build_black_prompt(q, yellow_v, prev): ...
def build_blue_prompt(q, yellow_v, black_v, yellow_vote="neutral", black_vote="neutral"): ...

# Voting logic
def handle_vote(role, idx, vote_type):
    other = "dislike" if vote_type == "like" else "like"
    st.session_state.votes[f"{role}_{idx}"] = vote_type
    st.session_state.votes.pop(f"{role}_{idx}_{other}", None)

# Render card
def render_card(role, data, idx):
    with st.container():
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

# Show rounds
for i, r in enumerate(st.session_state.rounds):
    st.markdown(f"## 🎯 {T['round_title'][lang]} {i+1}")
    col1, col2 = st.columns(2)
    with col1: render_card("yellow", r["yellow"], i)
    with col2: render_card("black", r["black"], i)

# Trigger new round
if st.button(T["start"][lang] if len(st.session_state.rounds) == 0 else T["continue"][lang]) and question:
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

    yellow_view = yellow['card_1']['content']['viewpoint'] if yellow_vote == "like" or not prev else ""
    with st.spinner("Generating Black Hat..."):
        b_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_black_prompt(question, yellow_view, prev)}],
            temperature=0.7
        ).choices[0].message.content
        black = safe_json_parse(b_raw, "Black Hat")

    st.session_state.rounds.append({"yellow": yellow, "black": black})
    st.rerun()

# Blue Hat summary
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
            blue = safe_json_parse(blue_raw, "Blue Hat")
            st.session_state.final_summary = blue["card"]["content"]

    st.markdown(f"### {T['final_summary'][lang]}")
    st.markdown(st.session_state.final_summary)

# -- placeholder: JSON parsing function
def safe_json_parse(raw, label):  # 保持之前的逻辑
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
