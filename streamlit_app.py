import streamlit as st
import json
from openai import OpenAI

# ✅ Must be the very first Streamlit command
st.set_page_config(page_title="Six Thinking Hats · AI Debate", layout="wide")

# ✅ Text dictionary (English only)
T = {
    "title": "🧠 Six Thinking Hats · AI Debate Guide",
    "question_input": "Enter your question:",
    "question_ph": "e.g., Should I quit my job?",
    "start": "Start First Round",
    "continue": "🔁 Continue Battle",
    "round_title": "Round",
    "summarize": "🗞️ Summarize All Viewpoints",
    "final_summary": "🔷 Final Blue Hat Summary",
    "support": "👍 Support",
    "oppose": "👎 Oppose",
    "voted_support": "[✓] Supported",
    "voted_oppose": "[X] Opposed",
    "thinking_train": "🧠 Expand Thinking Practice"
}

# ✅ Page title
st.title(T["title"])

# ✅ Question input
question = st.text_input(T["question_input"], placeholder=T["question_ph"])

# ✅ App state
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "votes" not in st.session_state:
    st.session_state.votes = {}
if "final_summary" not in st.session_state:
    st.session_state.final_summary = None

# ✅ OpenAI client
api_key = st.secrets["DEEPSEEK_API_KEY"]
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# ✅ JSON safe parser
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

# ✅ Prompt builders
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

# ✅ Voting logic
def handle_vote(role, idx, vote_type):
    other = "dislike" if vote_type == "like" else "like"
    st.session_state.votes[f"{role}_{idx}"] = vote_type
    st.session_state.votes.pop(f"{role}_{idx}_{other}", None)

# ✅ Render debate card
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
        label = T["voted_support"] if vote_status == "like" else T["support"]
        if st.button(label, key=f"like_{role}_{idx}"):
            handle_vote(role, idx, "like")
    with c2:
        label = T["voted_oppose"] if vote_status == "dislike" else T["oppose"]
        if st.button(label, key=f"dislike_{role}_{idx}"):
            handle_vote(role, idx, "dislike")

    if st.toggle(T["thinking_train"], key=f"train_{role}_{idx}"):
        st.markdown(data["card_2"]["content"]["thinking_path"])
        st.markdown(data["card_2"]["content"]["training_tip"])

# ✅ Show past rounds
for i, r in enumerate(st.session_state.rounds):
    st.markdown(f"## 🎯 {T['round_title']} {i+1}")
    col1, col2 = st.columns(2)
    with col1: render_card("yellow", r["yellow"], i)
    with col2: render_card("black", r["black"], i)

# ✅ Trigger new round
yellow = black = None
if st.button(T["start"] if not st.session_state.rounds else T["continue"]) and question:
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

# ✅ Final summary
if st.button(T["summarize"]) and st.session_state.rounds:
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

    st.markdown(f"### {T['final_summary']}")
    st.markdown(st.session_state.final_summary)
