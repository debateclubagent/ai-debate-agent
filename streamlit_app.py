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

# Prompt 构建函数（略）
# build_yellow_prompt / build_black_prompt / build_blue_prompt

# 页面设置与初始化
st.set_page_config(page_title="六顶思考帽 · AI 辩论器", layout="wide")
st.title("🧠 六顶思考帽 · AI 辩论引导")

question = st.text_input("请输入你的问题：", placeholder="例如：我要不要离职")
if "rounds" not in st.session_state:
    st.session_state.rounds = []
if "votes" not in st.session_state:
    st.session_state.votes = {}

# 生成新一轮观点按钮
if st.button("开始第一轮" if len(st.session_state.rounds) == 0 else "🔁 接着 Battle") and question:
    previous_rounds = st.session_state.rounds

    with st.spinner("黄帽思考中..."):
        yellow_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_yellow_prompt(question, previous_rounds)}],
            temperature=0.7
        ).choices[0].message.content
        yellow = safe_json_parse(yellow_raw, "黄帽")

    yellow_view = yellow['card_1']['content']['viewpoint']
    if len(previous_rounds) > 0 and st.session_state.votes.get(f"like_yellow_{len(previous_rounds)-1}") != True:
        yellow_view = ""

    with st.spinner("黑帽反思中..."):
        black_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_black_prompt(question, yellow_view, previous_rounds)}],
            temperature=0.7
        ).choices[0].message.content
        black = safe_json_parse(black_raw, "黑帽")

    black_view = black['card_1']['content']['viewpoint']
    if len(previous_rounds) > 0 and st.session_state.votes.get(f"like_black_{len(previous_rounds)-1}") != True:
        black_view = ""

    with st.spinner("蓝帽总结中..."):
        blue_raw = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": build_blue_prompt(question, yellow_view, black_view)}],
            temperature=0.7
        ).choices[0].message.content
        blue = safe_json_parse(blue_raw, "蓝帽")

    st.session_state.rounds.append({"yellow": yellow, "black": black, "blue": blue})
    st.rerun()

# 观点展示区（并排 + 点赞独立）
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

            if role in ["yellow", "black"]:
                card2 = card.get("card_2", {})
                if card2:
                    st.markdown(f"**{card2['title']}**")
                    st.markdown(card2["content"].get("thinking_path", ""))
                    st.markdown(card2["content"].get("training_tip", ""))

            cols = st.columns(2)
            with cols[0]:
                if st.button("👍 喜欢" + (" ✅" if is_liked else ""), key=vote_like_key):
                    st.session_state.votes[vote_like_key] = not is_liked
                    if is_liked:
                        st.session_state.votes[vote_dislike_key] = False
            with cols[1]:
                if st.button("👎 不喜欢" + (" ✅" if is_disliked else ""), key=vote_dislike_key):
                    st.session_state.votes[vote_dislike_key] = not is_disliked
                    if is_disliked:
                        st.session_state.votes[vote_like_key] = False

            if is_liked:
                st.success("你赞同了这个观点")
            elif is_disliked:
                st.error("你不赞同这个观点")
