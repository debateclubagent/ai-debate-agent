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
...
