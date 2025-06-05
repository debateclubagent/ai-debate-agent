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
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        st.error(f"⚠️ {label} 的输出不是合法 JSON：{e}")
        st.text_area("原始返回内容", raw, height=300)
        return None

# 三顶帽子 prompt 构建函数（略，与你已有版本一致）
# 省略了 build_yellow_prompt、build_black_prompt、build_blue_prompt
# 请参考你已有代码，将这三段原封不动粘贴回来

# 主函数部分
st.set_page_config(page_title="六顶思考帽 AI", layout="wide")
st.title("🎩 六顶思考帽：AI 观点生成器")
question = st.text_area("请输入你的问题：", placeholder="例如：我该不该先免费提供产品？")

if st.button("生成多角色观点"):
    if not question:
        st.warning("请输入一个问题！")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.spinner("🟡 黄帽思考中..."):
            yellow_prompt = build_yellow_prompt(question)
            yellow_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": yellow_prompt}]
            )
            yellow_json = safe_json_parse(yellow_response.choices[0].message.content, "黄帽")
            if yellow_json:
                st.markdown(f"**{yellow_json['card_a']['title']}**")
                st.write(yellow_json['card_a']['content']['viewpoint'])
                st.write(yellow_json['card_a']['content']['evidence'])
                st.markdown(f"**{yellow_json['card_b']['title']}**")
                st.write(yellow_json['card_b']['content']['thinking_path'])
                st.write(yellow_json['card_b']['content']['training_tip'])

    with col2:
        with st.spinner("⚫ 黑帽反思中..."):
            if not yellow_json:
                st.warning("⚠️ 无法生成黑帽观点，黄帽生成失败")
                st.stop()
            yellow_viewpoint = yellow_json['card_a']['content']['viewpoint']
            black_prompt = build_black_prompt(question, yellow_viewpoint)
            black_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": black_prompt}]
            )
            black_json = safe_json_parse(black_response.choices[0].message.content, "黑帽")
            if black_json:
                st.markdown(f"**{black_json['card_a']['title']}**")
                st.write(black_json['card_a']['content']['viewpoint'])
                st.write(black_json['card_a']['content']['evidence'])
                st.markdown(f"**{black_json['card_b']['title']}**")
                st.write(black_json['card_b']['content']['thinking_path'])
                st.write(black_json['card_b']['content']['training_tip'])

    with col3:
        with st.spinner("🔵 蓝帽总结中..."):
            if not yellow_json or not black_json:
                st.warning("⚠️ 无法生成蓝帽总结，前置观点缺失")
                st.stop()
            black_viewpoint = black_json['card_a']['content']['viewpoint']
            blue_prompt = build_blue_prompt(question, yellow_viewpoint, black_viewpoint)
            blue_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": blue_prompt}]
            )
            blue_json = safe_json_parse(blue_response.choices[0].message.content, "蓝帽")
            if blue_json:
                st.markdown(f"**{blue_json['card']['title']}**")
                st.write(blue_json['card']['content'])
