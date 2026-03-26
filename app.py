import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢")

# 2. 제목 및 설명
st.title("🚢 루버 블레이드 설계 관제 시스템")
st.info("Capstone Design: Chosun Sidae (조선시대) - 박재영 팀장님 환영합니다.")

# 3. 간단한 챗봇 인터페이스
if prompt := st.chat_input("설계 목표나 질문을 입력하세요"):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 여기에 나중에 AI 로직을 연결할 수 있습니다.
        st.write(f"'{prompt}'에 대한 해석 데이터를 로드 중입니다... (Star-CCM+ 연동 준비)")