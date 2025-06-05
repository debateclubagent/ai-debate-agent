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

# 统一的 JSON 解析保护函数
def safe_json_parse(raw, label):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        st.error(f"⚠️ {label} 的输出不是合法 JSON：{e}")
        st.text_area("原始返回内容", raw, height=300)
        return None

# 黄帽 Prompt
def build_yellow_prompt(question):
    return f"""
你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：{question}

请按以下四段进行回答：

### 🎯 1. 【我的观点】
请说出你对这个问题的积极判断。
你认为它最可能带来什么好处？你会从哪个角度看它“值得一试”？

### 📚 2. 【我的依据】
说明你为什么会这样判断。
你参考了哪些事实、常识、用户行为、案例或趋势？
重点在于：让人看懂你是“理性乐观”，不是瞎乐观。

### 🧠 3. 【我为什么会这样思考】
请从黄帽的视角解释你是如何找到这个“积极角度”的。
你可以说明：
- 黄帽通常关注什么（被低估的价值点？能激发正反馈的机制？用户感知入口？）
- 在这个问题里，你是怎么识别到“值得从希望切入”的机会点的？
- 这反映了黄帽惯常的什么思维方式？

### 🧩 4. 【你也可以这样练】
请提供一个简洁、有指向性的练习建议，帮助用户像黄帽一样思考：
- 如何识别一个“值得轻试”的积极入口？
- 如何在困难中刻意寻找“有转机的部分”？
- 如何从局部希望点出发，引导出一个判断过程？
重点在于：不是套模板，而是训练“看到希望值不值试”的能力。

请将你的回答封装为 JSON 对象，结构如下：
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
注意：请严格按照 JSON 格式输出，不要加解释、引言或 Markdown。
"""

# 黑帽 Prompt（引用黄帽观点）
def build_black_prompt(question, yellow_viewpoint):
    return f"""
你是“黑帽思维者”，你擅长发现风险、弱点和可能出问题的地方。
你的角色是从严谨、现实甚至悲观的角度看待问题，指出其中被忽略的隐患。

请你基于以下问题和“黄帽”的乐观观点，给出你的批判性思考：

用户的问题是：{question}
黄帽的乐观观点是：{yellow_viewpoint}

请按以下结构作答：

### ❗ 1. 【我的质疑】
指出黄帽观点中你认为过于乐观、忽略风险或缺乏论证的地方。

### 🧱 2. 【我的依据】
说明你这样怀疑的原因和依据。
你参考了哪些常识、失败经验、心理偏差、或对“乐观观点”的现实检验？

### ⚠️ 3. 【我为什么会这样思考】
请解释你的思考习惯：黑帽如何在想法萌芽时识别风险？
为什么你认为“泼冷水”也是必要的？

### 🧪 4. 【你也可以这样练】
请提供一个练习建议，帮助用户从黑帽的角度分析问题。

请将你的回答封装为 JSON 对象，结构如下：
{{
  "card_a": {{
    "title": "观点的负向判断",
    "content": {{
      "viewpoint": "❗ 我的质疑：...",
      "evidence": "🧱 我的依据：..."
    }}
  }},
  "card_b": {{
    "title": "思维方式与训练建议",
    "content": {{
      "thinking_path": "⚠️ 我为什么会这样思考：...",
      "training_tip": "🧪 你也可以这样练：..."
    }}
  }}
}}
注意：严格输出为 JSON 对象格式。
"""

# 蓝帽 Prompt（总结与判断）
def build_blue_prompt(question, yellow_viewpoint, black_viewpoint):
    return f"""
你是“蓝帽思维者”，你的任务是整合观点，做出理性判断和总结建议。

以下是用户的问题，以及黄帽与黑帽的主要观点：
问题：{question}
黄帽的核心观点：{yellow_viewpoint}
黑帽的核心观点：{black_viewpoint}

请你根据这两种思维模式的贡献，得出：

### 🧭 【总结与判断】
- 你认为两者分别看到了问题的哪些维度？
- 哪些部分你认同？哪些地方还需谨慎？
- 如果你是用户，你会怎么做？

请将总结封装为 JSON 格式：
{{
  "card": {{
    "title": "总结与判断",
    "content": "🧭 我的判断：..."
  }}
}}
"""

# 主函数
st.title("🎩 六顶思考帽：AI 观点生成器")
question = st.text_area("请输入你的问题：", placeholder="例如：我该不该先免费提供产品？")

if st.button("生成多角色观点"):
    if not question:
        st.warning("请输入一个问题！")
        st.stop()

    with st.spinner("🟡 黄帽思考中..."):
        yellow_prompt = build_yellow_prompt(question)
        yellow_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": yellow_prompt}]
        )
        yellow_json = safe_json_parse(yellow_response.choices[0].message.content, "黄帽")
        if yellow_json is None:
            st.stop()

        yellow_viewpoint = yellow_json['card_a']['content']['viewpoint']

    with st.spinner("⚫ 黑帽反思中..."):
        black_prompt = build_black_prompt(question, yellow_viewpoint)
        black_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": black_prompt}]
        )
        black_json = safe_json_parse(black_response.choices[0].message.content, "黑帽")
        if black_json is None:
            st.stop()

        black_viewpoint = black_json['card_a']['content']['viewpoint']

    with st.spinner("🔵 蓝帽总结中..."):
        blue_prompt = build_blue_prompt(question, yellow_viewpoint, black_viewpoint)
        blue_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": blue_prompt}]
        )
        blue_json = safe_json_parse(blue_response.choices[0].message.content, "蓝帽")
        if blue_json is None:
            st.stop()

    with st.expander("🟡 黄帽视角：乐观可能"):
        st.markdown(f"**{yellow_json['card_a']['title']}**")
        st.write(yellow_json['card_a']['content']['viewpoint'])
        st.write(yellow_json['card_a']['content']['evidence'])
        st.markdown(f"**{yellow_json['card_b']['title']}**")
        st.write(yellow_json['card_b']['content']['thinking_path'])
        st.write(yellow_json['card_b']['content']['training_tip'])

    with st.expander("⚫ 黑帽视角：质疑反思"):
        st.markdown(f"**{black_json['card_a']['title']}**")
        st.write(black_json['card_a']['content']['viewpoint'])
        st.write(black_json['card_a']['content']['evidence'])
        st.markdown(f"**{black_json['card_b']['title']}**")
        st.write(black_json['card_b']['content']['thinking_path'])
        st.write(black_json['card_b']['content']['training_tip'])

    with st.expander("🔵 蓝帽总结"):
        st.markdown(f"**{blue_json['card']['title']}**")
        st.write(blue_json['card']['content'])
