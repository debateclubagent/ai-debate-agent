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

def build_yellow_prompt(question):
    prompt = f"""
你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：{question}

请将你的回答封装为一个 JSON 对象，结构如下：

{{
  "card_a": {{
    "title": "问题的正向判断",
    "content": {{
      "viewpoint": "🎯 我的观点：...",
      "evidence": "📚 我的依据：..."
    }}
  }},
  "card_b": {{
    "title": "思维方式与训练建议",
    "content": {{
      "thinking_path": "🧠 我为什么会这样思考：...",
      "training_tip": "🧩 你也可以这样练：..."
    }}
  }}
}}
"""
    return prompt

def build_black_prompt(question, yellow_viewpoint):
    prompt = f"""
你是“黑帽思维者”，你擅长从问题中识别风险、隐患、失败代价，以及不能被轻易忽视的误判。
你不唱反调，但你习惯先问：“这里有什么我忽略的风险？”“这个方案失败的代价是否能承受？”

用户的问题是：{question}
黄帽给出的观点是：{yellow_viewpoint}

请你就着这个乐观判断，给出你的审慎分析，并指出用户可能忽略的盲区。

请将你的回答封装为一个 JSON 对象，结构如下：

{{
  "card_c": {{
    "title": "问题的反向质疑",
    "content": {{
      "doubt": "⚠️ 我的担忧：...",
      "evidence": "📌 我的依据：..."
    }}
  }},
  "card_d": {{
    "title": "谨慎思维方式与训练建议",
    "content": {{
      "thinking_path": "🧠 我为什么会这样思考：...",
      "training_tip": "🧩 你也可以这样练：..."
    }}
  }}
}}
"""
    return prompt

# Streamlit 页面结构
st.title("🧠 多帽思维生成器")

question = st.text_area("请输入你的问题：", height=120)

if st.button("生成黄帽 + 黑帽分析") and question:
    with st.spinner("正在生成，请稍候..."):
        try:
            # Step 1: 黄帽回答
            yellow_prompt = build_yellow_prompt(question)
            yellow_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个理性乐观、结构清晰的黄帽思维助理，只输出标准 JSON。"},
                    {"role": "user", "content": yellow_prompt}
                ],
                stream=False
            )
            yellow_reply = yellow_response.choices[0].message.content
            yellow_json = json.loads(yellow_reply[yellow_reply.find('{'):].split('```')[0].strip())
            yellow_viewpoint = yellow_json["card_a"]["content"]["viewpoint"]

            # Step 2: 黑帽跟进
            black_prompt = build_black_prompt(question, yellow_viewpoint)
            black_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个审慎思维者，只输出标准 JSON。"},
                    {"role": "user", "content": black_prompt}
                ],
                stream=False
            )
            black_reply = black_response.choices[0].message.content
            black_json = json.loads(black_reply[black_reply.find('{'):].split('```')[0].strip())

            # 展示黄帽卡片
            st.markdown("""
            <details open>
            <summary style='font-size: 20px; font-weight: bold;'>🟡 黄帽 · 问题的正向判断</summary>
            <div style='padding-left: 1em;'>
            <p>{}</p>
            <p>{}</p>
            </div>
            </details>
            <details open>
            <summary style='font-size: 20px; font-weight: bold;'>🟡 黄帽 · 思维方式与训练建议</summary>
            <div style='padding-left: 1em;'>
            <p>{}</p>
            <p>{}</p>
            </div>
            </details>
            """.format(
                yellow_json['card_a']['content']['viewpoint'],
                yellow_json['card_a']['content']['evidence'],
                yellow_json['card_b']['content']['thinking_path'],
                yellow_json['card_b']['content']['training_tip']
            ), unsafe_allow_html=True)

            # 展示黑帽卡片
            st.markdown("""
            <details open>
            <summary style='font-size: 20px; font-weight: bold;'>⚫ 黑帽 · 问题的反向质疑</summary>
            <div style='padding-left: 1em;'>
            <p>{}</p>
            <p>{}</p>
            </div>
            </details>
            <details open>
            <summary style='font-size: 20px; font-weight: bold;'>⚫ 黑帽 · 谨慎思维与训练建议</summary>
            <div style='padding-left: 1em;'>
            <p>{}</p>
            <p>{}</p>
            </div>
            </details>
            """.format(
                black_json['card_c']['content']['doubt'],
                black_json['card_c']['content']['evidence'],
                black_json['card_d']['content']['thinking_path'],
                black_json['card_d']['content']['training_tip']
            ), unsafe_allow_html=True)

        except Exception as e:
            st.error("⚠️ 出错了，请查看异常信息：")
            st.exception(e)
