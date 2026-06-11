import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Gemini 챗봇", page_icon="🤖", layout="wide")

# ── API 키: Streamlit Secrets에서 로드 ───────────────────────────────────────
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. Streamlit Cloud → Settings → Secrets에 GEMINI_API_KEY를 추가하세요.")
    st.stop()

# ── 사이드바: 설정 ────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 설정")

    model_name = st.selectbox(
        "모델 선택",
        ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
    )

    temperature = st.slider("Temperature", 0.0, 2.0, 1.0, 0.1,
                            help="높을수록 창의적, 낮을수록 일관적인 답변")

    system_prompt = st.text_area(
        "시스템 프롬프트 (선택)",
        placeholder="예) 당신은 친절한 한국어 어시스턴트입니다.",
        height=100,
    )

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat = None
        st.rerun()

    st.divider()
    st.caption("API 키는 브라우저 세션에만 저장되며 서버에 보관되지 않습니다.")

# ── 세션 초기화 ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = None
if "last_model" not in st.session_state:
    st.session_state.last_model = None

# ── 메인 영역 ────────────────────────────────────────────────────────────────
st.title("🤖 Gemini 챗봇")

# API 키 미입력 안내
if not api_key:
    st.info("👈 사이드바에 **Gemini API Key**를 입력하면 대화를 시작할 수 있습니다.")
    st.markdown(
        "API 키가 없다면 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 무료로 발급받으세요."
    )
    st.stop()

# 모델/설정 변경 시 채팅 세션 재생성
if st.session_state.last_model != (model_name, temperature, system_prompt):
    st.session_state.chat = None
    st.session_state.last_model = (model_name, temperature, system_prompt)

# Gemini 클라이언트 초기화
try:
    genai.configure(api_key=api_key)
    generation_config = genai.GenerationConfig(temperature=temperature)

    if st.session_state.chat is None:
        model_kwargs = {"generation_config": generation_config}
        if system_prompt.strip():
            model_kwargs["system_instruction"] = system_prompt.strip()

        model = genai.GenerativeModel(model_name, **model_kwargs)

        # 기존 메시지 히스토리로 채팅 복원
        history = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        st.session_state.chat = model.start_chat(history=history)

except Exception as e:
    st.error(f"API 초기화 실패: {e}")
    st.stop()

# ── 대화 기록 출력 ───────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 입력창 ───────────────────────────────────────────────────────────────────
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini 응답 (스트리밍)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        try:
            response = st.session_state.chat.send_message(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"❌ 오류가 발생했습니다: {e}"
            placeholder.error(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
