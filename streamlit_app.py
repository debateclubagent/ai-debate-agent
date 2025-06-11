import streamlit as st
import json
from openai import OpenAI

# Read API Key from Streamlit secrets
api_key = st.secrets["DEEPSEEK_API_KEY"]

# Initialize DeepSeek client
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# JSON parsing function
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

# Yellow hat prompt builder
def build_yellow_prompt(question, previous_rounds):
    ref = ""
    if previous_rounds:
        last_black = previous_rounds[-1].get("black", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_black:
            ref = f"\nPlease respond to the previous black hat viewpoint, especially the concerns or misjudgments raised: {last_black}"
    return f"""You are the "Yellow Hat Thinker". You are good at finding positive possibilities, underestimated benefits, and directions worth trying.
You don't deny difficulties, but you tend to ask yourself: “Is there something here that could bring a breakthrough?”

The user's question is: **{question}**{ref}

Please follow this JSON format and ensure it's valid:

{{
  "card_1": {{
    "title": "Positive Evaluation of the Question",
    "content": {{
      "viewpoint": "🎯 My Viewpoint: ...",
      "evidence": "📚 My Evidence: ..."
    }}
  }},
  "card_2": {{
    "title": "Thinking Style & Training Tips",
    "content": {{
      "thinking_path": "🧠 Why I Think This Way: ...",
      "training_tip": "🧩 You Can Practice Like This: ..."
    }}
  }}
}}"""

def build_black_prompt(question, yellow_viewpoint, previous_rounds):
    ref = ""
    if previous_rounds:
        last_yellow = previous_rounds[-1].get("yellow", {}).get("card_1", {}).get("content", {}).get("viewpoint", "")
        if last_yellow:
            ref = f"\nYou may also respond to the previous yellow hat viewpoint: {last_yellow}"
    return f"""You are the "Black Hat Thinker". You are skilled in identifying potential risks, uncontrollable factors, and overlooked limitations in problems.

The user's question is: **{question}**

Please reflect on and debate the "positive directions mentioned by the yellow hat":
You must respond to a specific yellow hat point, e.g., "The yellow hat mentioned..., but I think..."
Ensure the response is clear, targeted, and feels like a debate.

Yellow hat viewpoint: “{yellow_viewpoint}”{ref}

Please follow this JSON format and ensure it's valid:

{{
  "card_1": {{
    "title": "Potential Risks & Realistic Limitations",
    "content": {{
      "viewpoint": "💣 My Viewpoint: ...",
      "evidence": "📉 My Evidence: ..."
    }}
  }},
  "card_2": {{
    "title": "Thinking Style & Training Tips",
    "content": {{
      "thinking_path": "🧠 Why I Think This Way: ...",
      "training_tip": "🧩 You Can Practice Like This: ..."
    }}
  }}
}}"""

def build_blue_prompt(question, yellow_viewpoint, black_viewpoint, yellow_vote="neutral", black_vote="neutral"):
    vote_summary = {
        "like": "User supports this viewpoint ✅",
        "dislike": "User disagrees with this viewpoint ❌",
        "neutral": "User has no clear preference"
    }

    return f"""You are the "Blue Hat Thinker". Your job is to integrate the perspectives of the other two and help the user reach a rational judgment.

The user's question is: **{question}**

Yellow Hat viewpoint: “{yellow_viewpoint}”
→ {vote_summary.get(yellow_vote, 'None')}.

Black Hat viewpoint: “{black_viewpoint}”
→ {vote_summary.get(black_vote, 'None')}.

Based on the above, please do the following:
1. Compare the thought patterns of Yellow and Black Hat perspectives;
2. Reinforce the direction the user leans toward, helping them make an informed decision;
3. Provide your own recommendation or preference (balancing logic and emotion).

Please output valid JSON in this format (no explanation or backticks):

{{
  "card": {{
    "title": "Summary & Judgment",
    "content": "⚖️ My Conclusion: ..."
  }}
}}"""

# ✅ Page setup
st.set_page_config(page_title="Six Thinking Hats · AI Debater", layout="wide")
st.title("🧠 Six Thinking Hats · AI Debate Guide")

# ✅ State initialization
question = st.text_input("Enter your question:", placeholder="e.g., Should I quit my job?")
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "votes" not in st.session_state:
    st.session_state.votes = {}

# ✅ Voting logic
def handle_vote(role, idx, vote_type):
    other = "dislike" if vote_type == "like" else "like"
    st.session_state.votes[f"{role}_{idx}"] = vote_type
    st.session_state.votes.pop(f"{role}_{idx}_{other}", None)

# ✅ Card rendering logic
def render_card(role, data, idx):
    with st.container():
        st.markdown(f"### {'🟡 Yellow Hat' if role == 'yellow' else '⚫ Black Hat' if role == 'black' else '🔵 Blue Hat'}")
        card = data.get("card_1") or data.get("card")
        st.markdown(f"**{card['title']}**")
        st.markdown(card["content"]["viewpoint"] if isinstance(card["content"], dict) else card["content"])
        if isinstance(card["content"], dict) and "evidence" in card["content"]:
            st.markdown(card["content"]["evidence"])

        if role in ["yellow", "black"]:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👍 Support", key=f"like_{role}_{idx}"):
                    handle_vote(role, idx, "like")
            with c2:
                if st.button("👎 Oppose", key=f"dislike_{role}_{idx}"):
                    handle_vote(role, idx, "dislike")

            # Thinking training
            if st.toggle("🧠 Expand Thinking Practice", key=f"train_{role}_{idx}"):
                st.markdown(data["card_2"]["content"]["thinking_path"])
                st.markdown(data["card_2"]["content"]["training_tip"])

# ✅ Display rounds
for i, r in enumerate(st.session_state.rounds):
    st.markdown(f"## 🎯 Round {i+1}")
    col1, col2, col3 = st.columns(3)
    with col1: render_card("yellow", r["yellow"], i)
    with col2: render_card("black", r["black"], i)
    with col3: render_card("blue", r["blue"], i)

# ✅ Start / Next Round
if st.button("Start First Round" if len(st.session_state.rounds) == 0 else "🔁 Continue Battle") and question:
    prev = st.session_state.rounds
    yellow_vote = st.session_state.votes.get(f"yellow_{len(prev)-1}", "neutral") if prev else "neutral"
    black_vote = st.session_state.votes.get(f"black_{len(prev)-1}", "neutral") if prev else "neutral"

    yellow_input = "" if yellow_vote != "like" and prev else None
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

    black_view = black['card_1']['content']['viewpoint'] if black_vote == "like" or not prev else ""
    with st.spinner("Generating Blue Hat Summary..."):
        blue_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, yellow_view, black_view, yellow_vote, black_vote)}],
            temperature=0.7
        ).choices[0].message.content
        blue = safe_json_parse(blue_raw, "Blue Hat")

    st.session_state.rounds.append({"yellow": yellow, "black": black, "blue": blue})
    st.rerun()

# ✅ Final summary button
if st.button("🧾 Summarize All Viewpoints") and st.session_state.rounds:
    last = st.session_state.rounds[-1]
    y_view = last["yellow"]["card_1"]["content"]["viewpoint"]
    b_view = last["black"]["card_1"]["content"]["viewpoint"]
    y_vote = st.session_state.votes.get(f"yellow_{len(st.session_state.rounds)-1}", "neutral")
    b_vote = st.session_state.votes.get(f"black_{len(st.session_state.rounds)-1}", "neutral")
    with st.spinner("Generating Final Blue Hat Summary..."):
        summary_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, y_view, b_view, y_vote, b_vote)}],
            temperature=0.7
        ).choices[0].message.content
        summary = safe_json_parse(summary_raw, "Final Blue Hat")
        st.markdown("### 🔷 Final Blue Hat Summary")
        st.markdown(summary["card"]["content"])
