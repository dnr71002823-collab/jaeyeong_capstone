import streamlit as st
from groq import Groq

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢")
st.title("🚢 루버 블레이드 설계 관제 시스템")
st.info("Capstone Design: Chosun Saide (조선시대) - 박재영 팀장님 환영합니다.")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "너는 루버 블레이드 설계 전문 AI 어시스턴트야. "
                "유체역학, CFD(Star-CCM+), 열전달, 공기역학 관련 질문에 전문적으로 답변해. "
                "한국어로 답변해."
            )
        }
    ]

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("설계 목표나 질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
        )
        reply = response.choices[0].message.content
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})


