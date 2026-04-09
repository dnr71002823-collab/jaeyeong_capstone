import streamlit as st
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢")
st.title("🚢 루버 블레이드 설계 관제 시스템")
st.info("Capstone Design: Chosun Saide (조선시대) - 박재영 팀장님 환영합니다.")

SYSTEM_PROMPT = "너는 루버 블레이드 설계 전문 AI 어시스턴트야. 한국어로 답변해."

# 1. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    """시트에서 대화 이력 불러오기 (system 제외)"""
    try:
        df = conn.read(ttl=0)
        # 필수 컬럼 확인
        if df.empty or "역할" not in df.columns:
            return []
        records = df.to_dict("records")
        # system 메시지는 시트에서 제외하고 반환
        return [r for r in records if r.get("역할") in ("user", "assistant")]
    except Exception as e:
        st.warning(f"이력 불러오기 실패: {e}")
        return []

def save_pair(user_msg, assistant_msg):
    """유저+AI 응답을 한 번에 저장 (시트 접근 1회로 최소화)"""
    try:
        existing_df = conn.read(ttl=0)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_rows = pd.DataFrame([
            {"날짜": now, "역할": "user",      "내용": user_msg},
            {"날짜": now, "역할": "assistant", "내용": assistant_msg},
        ])
        updated_df = pd.concat([existing_df, new_rows], ignore_index=True)
        conn.update(data=updated_df)
    except Exception as e:
        st.error(f"데이터 저장 중 오류 발생: {e}")

# 2. 세션 상태 초기화 (최초 1회만 시트에서 불러오기)
if "messages" not in st.session_state:
    db_data = load_data()
    # system 프롬프트는 항상 맨 앞에 고정
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    if db_data:
        for m in db_data:
            st.session_state.messages.append({
                "role": m["역할"],
                "content": m["내용"]
            })

# 3. 대화 내용 출력 (system 제외)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. 사용자 입력 처리
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if prompt := st.chat_input("설계 목표나 질문을 입력하세요"):
    # 유저 메시지 즉시 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 (스트리밍)
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            stream=True,  # ✅ 스트리밍 활성화
        )
        reply = st.write_stream(
            chunk.choices[0].delta.content or ""
            for chunk in stream
        )

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # ✅ 유저 + AI 응답을 한 번에 저장
    save_pair(prompt, reply)
