import streamlit as st
from functions import initial_server

initial_server()

title = "Shadow Home"

st.set_page_config(
    page_icon="🖥️",
    page_title=title,
)

# CSS 스타일을 추가합니다
st.markdown(
    """
<style>
    h1 {
        color: #4A90E2;  # Bright blue color
        font-family: "Helvetica", sans-serif;
        margin-bottom: 0.5em;  # Add space below the title
    }
    .welcome-message {
        font-size:20px !important;
        color: #333333;  # Dark grey
        font-family: "Arial", sans-serif;
        margin-bottom: 1em;  # Add space below the welcome message
        line-height: 1.5;  # Increase line spacing
    }
    .feature {
        font-size:18px !important;
        color: #204780;
        font-family: "Arial", sans-serif;
        margin-bottom: 10px;
    }
    .sub-feature {
        font-size:16px !important;
        color: #555555;  # Medium grey
        margin-left: 20px;
        margin-bottom: 0.8em;  # Add space below each sub-feature
    }
    .big-font {
        font-size:22px !important;
        font-weight:bold;
        color: #4A90E2;  # Bright blue
        font-family: "Arial", sans-serif;
        margin-top: 1em;  # Add space above the section title
        margin-bottom: 0.5em;  # Add space below the section title
    }
    .tech-style {
        font-size:16px;
        background-color: #f4f4f9;  # Light grey background
        border-left: 5px solid #4A90E2;  # Bright blue border
        padding: 10px;
        margin-bottom: 1em;  # Add space below the tech style box
    }
</style>
""",
    unsafe_allow_html=True,
)

# 상단의 타이틀과 아이콘 설정
st.title(title)
st.image("youtube.png", width=80)  # AI-themed 로고 이미지를 추가할 경우

# 홈 화면에 대한 환영 메시지와 앱 설명
st.markdown(
    """
    <div class="welcome-message">환영합니다, 방문자 여러분! 🌍</div>
    <div class="tech-style">
    Shadow Home은 재미있는 방식으로 여러분의 영어 실력 향상을 도와주는 AI 기반 앱입니다!
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    여러분은 다음과 같은 방법으로 영어를 배울 수 있습니다:
    - 📹 좋아하는 유튜버, 다큐멘터리 등의 비디오를 보면서
    - 🎧 팟캐스트나 다른 오디오 소스를 들으면서
""",
    unsafe_allow_html=True,
)

# 앱의 주요 기능 소개
st.markdown(
    """
    <div class="big-font">주요 기능</div>

    <div class="feature">1. 비디오 업로드 및 자동화된 자막 추출 시스템</div>
    <div class="sub-feature">- 비디오나 오디오 파일을 업로드하면 자동으로 자막을 생성해줍니다.</div>

    <div class="feature">2. 비디오 선택 및 자막 기능</div>
    <div class="sub-feature">- 업로드된 비디오 중에서 선택하여 재생할 수 있으며, 자막을 통해 학습을 도울 수 있습니다.</div>

    <div class="feature">3. LangChain 기반 영어 빈칸 퀴즈 생성기</div>
    <div class="sub-feature">- 업로드한 문서나 텍스트로부터 영어 빈칸 퀴즈를 생성하여 영어 실력을 시험해 볼 수 있습니다.</div>
""",
    unsafe_allow_html=True,
)
