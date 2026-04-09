import streamlit as st
from groq import Groq
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢")
st.title("🚢 루버 블레이드 설계 관제 시스템")
st.info("Capstone Design: Chosun Saide (조선시대) - 박재영 팀장님 환영합니다.")

SYSTEM_PROMPT = "너는 루버 블레이드 설계 전문 AI 어시스턴트야. 한국어로 답변해."
CSV_FILE = "chat_history.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        return df.to_dict("records")
    return []

def save_pair(user_msg, assistant_msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_rows = pd.DataFrame([
        {"날짜": now, "역할": "user",      "내용": user_msg},
        {"날짜": now, "역할": "assistant", "내용": assistant_msg},
    ])
    if os.path.exists(CSV_FILE):
        existing = pd.read_csv(CSV_FILE)
        updated = pd.concat([existing, new_rows], ignore_index=True)
    else:
        updated = new_rows
    updated.to_csv(CSV_FILE, index=False)

# 세션 초기화
if "messages" not in st.session_state:
    db_data = load_data()
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in db_data:
        st.session_state.messages.append({"role": m["역할"], "content": m["내용"]})

# 대화 출력
for msg in st.session_state.messages:
    if msg["role"] == "system": continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 입력 처리
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if prompt := st.chat_input("설계 목표나 질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            stream=True,
        )
        reply = st.write_stream(
            chunk.choices[0].delta.content or ""
            for chunk in stream
        )

    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_pair(prompt, reply)
