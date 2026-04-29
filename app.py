import streamlit as st
from groq import Groq
from datetime import datetime
import os, json, uuid
from supabase import create_client

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢", layout="wide")

# Supabase 클라이언트 (에러 핸들링 추가)
try:
    supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
except Exception as e:
    st.error(f"Supabase 연결 실패: {e}")
    st.info("Secrets 설정을 확인하세요. Settings → Secrets에서 supabase.url과 supabase.key를 설정해야 합니다.")
    st.stop()

BLADE_KEYWORDS = ["루버", "블레이드", "각도", "풍속", "재질", "설계", "압력", "유량", "두께", "간격", "프레임"]

def build_system_prompt():
    """Supabase 과거 대화에서 루버 블레이드 관련 내용만 추출해서 SYSTEM_PROMPT에 주입"""
    try:
        all_sessions = supabase.table("chat_sessions").select("messages").execute()
        history = ""
        for session in all_sessions.data:
            for msg in session["messages"]:
                if msg["role"] == "system":
                    continue
                if any(kw in msg["content"] for kw in BLADE_KEYWORDS):
                    role = "사용자" if msg["role"] == "user" else "AI"
                    history += f"{role}: {msg['content']}\n"
        history = history[-4000:]  # 토큰 제한: 최근 4000자만
    except Exception as e:
        st.warning(f"과거 대화 불러오기 실패: {e}")
        history = ""

    return f"""너는 루버 블레이드 설계 전문 AI 어시스턴트야. 한국어로 답변해.

## 과거 대화에서 학습한 루버 블레이드 설계 내용:
{history if history else "아직 없음"}

위 내용을 바탕으로 사용자의 설계 의도와 맥락을 파악해서 답변해."""

def list_sessions():
    try:
        res = supabase.table("chat_sessions").select("id, title, date").order("date", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"세션 목록 불러오기 실패: {e}")
        return []

def load_session(session_id):
    try:
        res = supabase.table("chat_sessions").select("*").eq("id", session_id).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        st.error(f"세션 불러오기 실패: {e}")
        return None

def save_session(session_id, title, messages):
    try:
        supabase.table("chat_sessions").upsert({
            "id": session_id,
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "messages": messages
        }).execute()
    except Exception as e:
        st.error(f"세션 저장 실패: {e}")

def delete_session(session_id):
    try:
        supabase.table("chat_sessions").delete().eq("id", session_id).execute()
    except Exception as e:
        st.error(f"세션 삭제 실패: {e}")

def make_title(prompt):
    return prompt[:15] + "..." if len(prompt) > 15 else prompt

# 세션 상태 초기화 (새 대화 시작 시 과거 대화 포함한 system prompt 주입)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "system", "content": build_system_prompt()}]
    st.session_state.title = "새 대화"

# 사이드바
with st.sidebar:
    st.title("🚢 대화 목록")
    if st.button("+ 새 대화", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        # 새 대화 시작할 때마다 최신 과거 대화 내용 반영
        st.session_state.messages = [{"role": "system", "content": build_system_prompt()}]
        st.session_state.title = "새 대화"
        st.rerun()
    st.divider()

    for s in list_sessions():
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(f"💬 {s['title']}\n{s['date']}", key=s["id"], use_container_width=True):
                data = load_session(s["id"])
                if data:
                    st.session_state.session_id = s["id"]
                    st.session_state.messages = data["messages"]
                    st.session_state.title = data["title"]
                    st.rerun()
        with col2:
            if st.button("삭제", key=f"del_{s['id']}"):
                delete_session(s["id"])
                if st.session_state.session_id == s["id"]:
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = [{"role": "system", "content": build_system_prompt()}]
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
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                stream=True,
            )
            reply = st.write_stream(
                chunk.choices[0].delta.content or "" for chunk in stream
            )
        except Exception as e:
            st.error(f"AI 응답 생성 실패: {e}")
            reply = "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."

    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_session(st.session_state.session_id, st.session_state.title, st.session_state.messages)
