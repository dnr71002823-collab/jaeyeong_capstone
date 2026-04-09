import streamlit as st
from groq import Groq
import pandas as pd
from datetime import datetime
import os, json, uuid, base64, requests

st.set_page_config(page_title="조선시대 관제 시스템", page_icon="🚢", layout="wide")

SYSTEM_PROMPT = "너는 루버 블레이드 설계 전문 AI 어시스턴트야. 한국어로 답변해."
HISTORY_DIR = "chat_sessions"
os.makedirs(HISTORY_DIR, exist_ok=True)

GITHUB_TOKEN = "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"
GITHUB_REPO  = "dnr71002823/jaeyeong_capstone"
GITHUB_BRANCH = "main"

# ── GitHub 저장 함수 ──────────────────────
def github_upload(filename, content_dict):
    """JSON을 GitHub 레포에 업로드/덮어쓰기"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/chat_sessions/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    content_b64 = base64.b64encode(
        json.dumps(content_dict, ensure_ascii=False).encode()
    ).decode()

    # 기존 파일 SHA 확인 (덮어쓰기용)
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    payload = {
        "message": f"chat update: {filename}",
        "content": content_b64,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    requests.put(url, headers=headers, json=payload)

def github_load_all():
    """GitHub에서 모든 세션 JSON 불러오기"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/chat_sessions"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return []
    files = r.json()
    sessions = []
    for f in sorted(files, key=lambda x: x["name"], reverse=True):
        content_r = requests.get(f["download_url"], headers=headers)
        data = content_r.json()
        sessions.append({
            "id": f["name"].replace(".json", ""),
            "title": data.get("title", "새 대화"),
            "date": data.get("date", ""),
            "messages": data.get("messages", [])
        })
    return sessions

# ── 로컬 + GitHub 저장 ────────────────────
def save_session(session_id, title, messages):
    data = {
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "messages": messages
    }
    # 로컬 저장
    with open(f"{HISTORY_DIR}/{session_id}.json", "w") as f:
        json.dump(data, f, ensure_ascii=False)
    # GitHub 저장
    github_upload(f"{session_id}.json", data)

def make_title(prompt):
    return prompt[:15] + "..." if len(prompt) > 15 else prompt

# ── 세션 목록 캐시 ────────────────────────
if "all_sessions" not in st.session_state:
    with st.spinner("이전 대화 불러오는 중..."):
        st.session_state.all_sessions = github_load_all()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.title = "새 대화"

# ── 사이드바 ──────────────────────────────
with st.sidebar:
    st.title("🚢 대화 목록")
    if st.button("+ 새 대화", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.title = "새 대화"
        st.rerun()

    if st.button("🔄 목록 새로고침", use_container_width=True):
        with st.spinner("불러오는 중..."):
            st.session_state.all_sessions = github_load_all()
        st.rerun()

    st.divider()
    for s in st.session_state.all_sessions:
        if st.button(f"💬 {s['title']}\n{s['date']}", key=s["id"], use_container_width=True):
            st.session_state.session_id = s["id"]
            st.session_state.messages = s["messages"]
            st.session_state.title = s["title"]
            st.rerun()

# ── 메인 화면 ─────────────────────────────
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

    # 세션 목록 갱신
    st.session_state.all_sessions = github_load_all()
