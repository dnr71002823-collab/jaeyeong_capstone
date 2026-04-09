import streamlit as st
from groq import Groq
from datetime import datetime
import os, json, uuid
from supabase import create_client

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢", layout="wide")

SYSTEM_PROMPT = "너는 루버 블레이드 설계 전문 AI 어시스턴트야. 한국어로 답변해."

# Supabase 클라이언트
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

def list_sessions():
    res = supabase.table("chat_sessions").select("id, title, date").order("date", desc=True).execute()
    return res.data or []

def load_session(session_id):
    res = supabase.table("chat_sessions").select("*").eq("id", session_id).execute()
    if res.data:
        return res.data[0]
    return None

def save_session(session_id, title, messages):
    supabase.table("chat_sessions").upsert({
        "id": session_id,
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "messages": messages
    }).execute()

def delete_session(session_id):
    supabase.table("chat_sessions").delete().eq("id", session_id).execute()

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
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(f"💬 {s['title']}\n{s['date']}", key=s["id"], use_container_width=True):
                data = load_session(s["id"])
                st.session_state.session_id = s["id"]
                st.session_state.messages = data["messages"]
                st.session_state.title = data["title"]
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{s['id']}"):
                delete_session(s["id"])
                # 현재 보고 있던 대화가 삭제된 경우 새 대화로 초기화
                if st.session_state.session_id == s["id"]:
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                    st.session_state.title = "새 대화"
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
