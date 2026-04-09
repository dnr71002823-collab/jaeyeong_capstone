import streamlit as st
from groq import Groq
import pandas as pd
from datetime import datetime
import os, json, uuid

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢", layout="wide")

SYSTEM_PROMPT = "너는 루버 블레이드 설계 전문 AI 어시스턴트야. 한국어로 답변해."
HISTORY_DIR = "chat_sessions"
os.makedirs(HISTORY_DIR, exist_ok=True)

def list_sessions():
    files = sorted(
        [f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")],
        reverse=True
    )
    sessions = []
    for f in files:
        with open(f"{HISTORY_DIR}/{f}") as fp:
            data = json.load(fp)
            sessions.append({
                "id": f.replace(".json", ""),
                "title": data.get("title", "새 대화"),
                "date": data.get("date", "")
            })
    return sessions

def load_session(session_id):
    path = f"{HISTORY_DIR}/{session_id}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def save_session(session_id, title, messages):
    path = f"{HISTORY_DIR}/{session_id}.json"
    with open(path, "w") as f:
        json.dump({
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "messages": messages
        }, f, ensure_ascii=False)

def make_title(prompt):
    return prompt[:15] + "..." if len(prompt) > 15 else prompt

# 세션 상태 초기화
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.title = "새 대화"

# 사이드바
with st.sidebar:
    st.title("🚢 대화 목록")
    if st.button("+ 새 대화", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.title = "새 대화"
        st.rerun()

    st.divider()
    for s in list_sessions():
        if st.button(f"💬 {s['title']}\n{s['date']}", key=s["id"], use_container_width=True):
            data = load_session(s["id"])
            st.session_state.session_id = s["id"]
            st.session_state.messages = data["messages"]
            st.session_state.title = data["title"]
            st.rerun()

# 메인 화면
st.title(f"🚢 {st.session_state.title}")
st.info("Capstone Design: Chosun Saide (조선시대) - 박재영 팀장님 환영합니다.")

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if prompt := st.chat_input("설계 목표나 질문을 입력하세요"):
    if st.session_state.title == "새 대화":
        st.session_state.title = make_title(prompt)

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
            chunk.choices[0].delta.content or "" for chunk in stream
        )

    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_session(st.session_state.session_id, st.session_state.title, st.session_state.messages)
