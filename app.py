import streamlit as st
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢")
st.title("🚢 루버 블레이드 설계 관제 시스템")
st.info("Capstone Design: Chosun Saide (조선시대) - 박재영 팀장님 환영합니다.")

# 1. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(ttl=0)
        return df.to_dict('records')
    except:
        return []

def save_data(role, content):
    try:
        existing_df = conn.read(ttl=0)
        new_row = pd.DataFrame([{
            "날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "역할": role,
            "내용": content
        }])
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        conn.update(data=updated_df)
    except Exception as e:
        st.error(f"데이터 저장 중 오류 발생: {e}")

# 2. 세션 상태 초기화 (시트에서 불러오기)
if "messages" not in st.session_state:
    db_data = load_data()
    if not db_data:
        st.session_state.messages = [
            {"role": "system", "content": "너는 루버 블레이드 설계 전문 AI 어시스턴트야. 한국어로 답변해."}
        ]
    else:
        # 시트 데이터(역할, 내용)를 AI가 이해하는 형식으로 변환하여 로드
        st.session_state.messages = [{"role": m["역할"], "content": m["내용"]} for m in db_data]

# 3. 대화 내용 출력
for msg in st.session_state.messages:
    if msg["role"] == "system": continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. 사용자 입력 처리
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if prompt := st.chat_input("설계 목표나 질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    save_data("user", prompt) # 시트에 사용자 질문 저장

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
        )
        reply = response.choices[0].message.content
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_data("assistant", reply) # 시트에 AI 답변 저장
