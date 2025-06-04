import streamlit as st
import json
from openai import OpenAI
import os

# 从 Streamlit secrets 读取 API Key
api_key = st.secrets["DEEPSEEK_API_KEY"]

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com/v1"
)

def build_prompt(question):
    return f"""
你是“黄帽思维者”，你擅长从问题中发现积极可能、被低估的好处，以及值得轻试的方向。
你不否认困难，但你习惯优先问自己：“这里有没有什么地方，是可以带来转机的？”

用户的问题是：**{question}**

请按以下四段进行回答：

---

### 🎯 1. 【我的观点】

请说出你对这个问题的积极判断。
你认为它最可能带来什么好处？你会从哪个角度看它“值得一试”？

---

### 📚 2. 【我的依据】

说明你为什么会这样判断。
你参考了哪些事实、常识、用户行为、案例或趋势？
重点在于：**让人看懂你是“理性乐观”，不是瞎乐观。**

---

### 🧠 3. 【我为什么会这样思考】

请从**黄帽的视角**解释你是如何找到这个“积极角度”的。

你可以说明：

* 黄帽通常关注什么（被低估的价值点？能激发正反馈的机制？用户感知入口？）
* 在这个问题里，你是怎么识别到“值得从希望切入”的机会点的？
* 这反映了黄帽惯常的什么思维方式？

---

### 🧩 4. 【你也可以这样练】

请提供一个简洁、有指向性的练习建议，帮助用户像黄帽一样思考：

* 如何识别一个“值得轻试”的积极入口？
* 如何在困难中刻意寻找“有转机的部分”？
* 如何从局部希望点出发，引导出一个判断过程？

重点在于：**不是套模板，而是训练“看到希望值不值试”的能力。**

请输出以下格式内容（注意是**标准 JSON 对象**，**不是字符串**，不要加转义符号）：

```json
{
  "card_a": {
    "title": "问题的正向判断",
    "content": {
      "viewpoint": "🎯 我的观点：...",
      "evidence": "📚 我的依据：..."
    }
  },
  "card_b": {
    "title": "思维方式与训练建议",
    "content": {
      "thinking_path": "🧠 我为什么会这样思考：...",
      "training_tip": "🧩 你也可以这样练：..."
    }
  }
}
```"""

# Streamlit 页面结构
st.title("🟡 黄帽思维生成器")

question = st.text_area("请输入你的问题：", height=120)

if st.button("生成回答") and question:
    with st.spinner("正在生成，请稍候..."):
        try:
            prompt = build_prompt(question)

            response = client.chat.completions.create(
                model="deepseek-chat",  # 你也可以改为 'deepseek-reasoner'
                messages=[
                    {"role": "system", "content": "你是一个理性乐观的产品思维助理。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )

            reply = response.choices[0].message.content

            try:
                # 截取 JSON 部分
                json_start = reply.find('{')
                json_str = reply[json_start:].split('```')[0].strip()
                json_data = json.loads(json_str)

                st.subheader(json_data["card_a"]["title"])
                st.markdown(json_data["card_a"]["content"]["viewpoint"])
                st.markdown(json_data["card_a"]["content"]["evidence"])

                st.subheader(json_data["card_b"]["title"])
                st.markdown(json_data["card_b"]["content"]["thinking_path"])
                st.markdown(json_data["card_b"]["content"]["training_tip"])

            except Exception as e:
                st.error("⚠️ 无法解析为 JSON，请检查模型是否输出了合法 JSON 格式。")
                st.text(reply)

        except Exception as e:
            st.error("⚠️ 出错了，请查看下方原始输出：")
            st.text(reply)
            st.exception(e)
