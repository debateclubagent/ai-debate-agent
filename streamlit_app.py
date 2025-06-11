import streamlit as st
import json
from openai import OpenAI

# ✅ Must be the very first Streamlit command
st.set_page_config(page_title="Six Thinking Hats · AI Debate", layout="wide")

# ✅ Wrap text dictionary in a function to prevent early emoji rendering
def get_text_dict():
    return {
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

T = get_text_dict()

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
def build_yellow_prompt(q):
    return f"""You are the Yellow Hat Thinker. Be optimistic and find opportunities.\n\nQuestion: {q}\n\nReturn valid JSON:\n{{\n  \"card_1\": {{\n    \"title\": \"Positive Evaluation\",\n    \"content\": {{\n      \"viewpoint\": \"🎯 My Viewpoint: ...\",\n      \"evidence\": \"📚 My Evidence: ...\"\n    }}\n  }},\n  \"card_2\": {{\n    \"title\": \"Thinking Path & Training\",\n    \"content\": {{\n      \"thinking_path\": \"🧠 Why I think this way: ...\",\n      \"training_tip\": \"🧩 How you can train: ...\"\n    }}\n  }}\n}}"""

def build_black_prompt(q, yellow_view):
    return f"""You are the Black Hat Thinker. Spot risks and downsides.\n\nQuestion: {q}\n\nYellow Hat said: {yellow_view}\n\nReturn valid JSON:\n{{\n  \"card_1\": {{\n    \"title\": \"Risks & Limitations\",\n    \"content\": {{\n      \"viewpoint\": \"💣 My Viewpoint: ...\",\n      \"evidence\": \"📉 My Evidence: ...\"\n    }}\n  }},\n  \"card_2\": {{\n    \"title\": \"Thinking Path & Training\",\n    \"content\": {{\n      \"thinking_path\": \"🧠 Why I think this way: ...\",\n      \"training_tip\": \"🧩 How you can train: ...\"\n    }}\n  }}\n}}"""

def build_blue_prompt(q, yellow_v, black_v, y_vote, b_vote):
    return f"""You are the Blue Hat Thinker. Summarize both perspectives and help reach a conclusion.\n\nQuestion: {q}\n\nYellow: {yellow_v} (vote: {y_vote})\nBlack: {black_v} (vote: {b_vote})\n\nReturn this JSON:\n{{\n  \"card\": {{\n    \"title\": \"Summary & Judgment\",\n    \"content\": \"⚖️ My conclusion: ...\"\n  }}\n}}"""

# ✅ Voting logic
def handle_vote(role, idx, vote_type):
    st.session_state.votes[f"{role}_{idx}"] = vote_type

# ✅ Render card
def render_card(role, data, idx):
    label = "🟡 Yellow Hat" if role == "yellow" else "⚫ Black Hat"
    st.markdown(f"### {label}")
    card = data.get("card_1")
    st.markdown(f"**{card['title']}**")
    st.markdown(card["content"].get("viewpoint", ""))
    if "evidence" in card["content"]:
        st.markdown(card["content"]["evidence"])

    vote_status = st.session_state.votes.get(f"{role}_{idx}", "neutral")
    col1, col2 = st.columns(2)
    with col1:
        label = T["voted_support"] if vote_status == "like" else T["support"]
        if st.button(label, key=f"like_{role}_{idx}"):
            handle_vote(role, idx, "like")
    with col2:
        label = T["voted_oppose"] if vote_status == "dislike" else T["oppose"]
        if st.button(label, key=f"dislike_{role}_{idx}"):
            handle_vote(role, idx, "dislike")

    if st.toggle(T["thinking_train"], key=f"train_{role}_{idx}"):
        st.markdown(data["card_2"]["content"].get("thinking_path", ""))
        st.markdown(data["card_2"]["content"].get("training_tip", ""))

# ✅ Display previous rounds
for i, r in enumerate(st.session_state.rounds):
    st.markdown(f"## 🎯 {T['round_title']} {i + 1}")
    col1, col2 = st.columns(2)
    with col1: render_card("yellow", r["yellow"], i)
    with col2: render_card("black", r["black"], i)

# ✅ Generate new round
yellow = black = None
if st.button(T["start"] if not st.session_state.rounds else T["continue"]) and question:
    with st.spinner("Generating Yellow Hat..."):
        y_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_yellow_prompt(question)}],
            temperature=0.7
        ).choices[0].message.content
        yellow = safe_json_parse(y_raw, "Yellow Hat")

    yellow_view = yellow['card_1']['content']['viewpoint']
    with st.spinner("Generating Black Hat..."):
        b_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_black_prompt(question, yellow_view)}],
            temperature=0.7
        ).choices[0].message.content
        black = safe_json_parse(b_raw, "Black Hat")

    st.session_state.rounds.append({"yellow": yellow, "black": black})
    st.rerun()

# ✅ Final blue hat summary
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
