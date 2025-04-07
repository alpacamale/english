import streamlit as st
import os
import openai
import random
import re
from dotenv import load_dotenv
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from gtts import gTTS

# 환경 설정
def setup_environment():
    load_dotenv()
    st.set_page_config(page_title="LangChain Quiz Generator", page_icon="📘")
    st.title("영어 빈칸 Quiz ❔🍪")
    return ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)

# 퀴즈 프롬프트 설정
def setup_quiz_chain(llm):
    quiz_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an English teacher."),
        ("human", """
    From the sentence below, make ONE multiple-choice fill-in-the-blank English quiz question.

    Instructions:
    - Replace ONE key word with a blank (____).
    - Provide exactly 4 options: A), B), C), D)
    - Only ONE option should be correct.
    - Mark the correct one with ✅
    - Format exactly like this:

    Question 1: I ____ to school every day.
    A) goes
    B) go ✅
    C) going
    D) gone

    Sentence: {sentence}
    """)
    ])
    return LLMChain(llm=llm, prompt=quiz_prompt)

# 파일 저장 (캐시 없음)
def save_uploaded_file(uploaded_file):
    file_path = f"./.cache/{uploaded_file.name}"
    os.makedirs(".cache", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path

# 파일 업로드 및 문장 추출
def upload_and_process_file():
    uploaded_file = st.file_uploader("📄 .txt 파일 업로드", type=["txt"])
    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)
        return extract_sentences_cached(file_path)
    return None

# 문장 추출 캐시
@st.cache_resource(show_spinner="📚 문장 추출 중...")
def extract_sentences_cached(file_path):
    return extract_sentences(file_path)

def extract_sentences(file_path):
    loader = TextLoader(file_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(separators=[".", "!", "?"], chunk_size=200, chunk_overlap=0)
    docs = splitter.split_documents(documents)
    sentences = [doc.page_content.strip() for doc in docs if len(doc.page_content.split()) > 4]
    if len(sentences) < 5:
        st.error("❗ 파일에 충분한 문장이 없습니다. 최소 5문장 이상 필요합니다.")
        return []
    return random.sample(sentences, min(20, len(sentences)))

# 퀴즈 생성 로직
def generate_and_display_quiz(quiz_chain, num_questions):
    if st.button("🎯 퀴즈 생성하기"):
        quiz_data = generate_quiz(quiz_chain, num_questions)
        st.session_state.quiz_data = quiz_data  # ← 퀴즈 데이터를 세션에 저장
        st.session_state.quiz_ready = True      # ← 퀴즈 준비 완료 플래그

        if len(quiz_data) < num_questions:
            st.warning(f"⚠️ GPT가 요청된 {num_questions}개의 퀴즈를 만들지 못했습니다. {len(quiz_data)}개만 생성되었습니다.")

def generate_quiz(quiz_chain, num_questions):
    quiz_data = []
    sentence_idx = 0큊
    attempts = 0  # 시도 횟수를 추적합니다.

    with st.spinner("🧠 GPT로 퀴즈 생성 중..."):
        # 필요한 문제 수를 충족할 때까지 반복하되, 무한 루프 방지를 위해 최대 시도 횟수 설정
        while len(quiz_data) < num_questions and attempts < num_questions * 3:
            # 문장 리스트를 순환하며 모든 문장을 사용하면 인덱스를 초기화
            if sentence_idx >= len(st.session_state.quiz_sentences):
                sentence_idx = 0

            s = st.session_state.quiz_sentences[sentence_idx]
            sentence_idx += 1
            result = quiz_chain.run({"sentence": s})
            parsed = parse_question_block(result)
            if parsed:
                parsed["source_sentence"] = s
                quiz_data.append(parsed)

            attempts += 1  # 시도 횟수를 업데이트합니다.

    # 최대 시도 횟수 내에 충분한 문제가 생성되지 않았다면 경고를 표시
    if len(quiz_data) < num_questions:
        st.warning(f"⚠️ GPT가 요청된 {num_questions}개의 퀴즈를 만들지 못했습니다. {len(quiz_data)}개만 생성되었습니다.")
    return quiz_data


# 퀴즈 결과 출력
def display_quiz_ui(quiz_data):
    st.subheader("📝 퀴즈 풀기")
    user_answers = {}
    with st.form("quiz_form"):
        for idx, q in enumerate(quiz_data):
            st.write(f"**Q{idx+1}. {q['question']}**")
            user_answers[idx] = st.radio("선택하세요:", q["options"], key=f"quiz_{idx}", index=None)
            st.markdown("---")
        submitted = st.form_submit_button("✅ 제출")
    if submitted:
        calculate_and_display_results(quiz_data, user_answers)


def calculate_and_display_results(quiz_data, user_answers):
    st.markdown("📊 채점 결과")

    score = 0
    total = len(quiz_data)

    # 각 문제 채점 결과 출력
    for idx, q in enumerate(quiz_data):
        user_ans = user_answers.get(idx)
        correct_ans = q["options"][q["answer"]]

        with st.container():
            st.markdown(f"**Q{idx + 1}. {q['question']}**")

            if user_ans is None:
                st.warning("🔸 선택하지 않았습니다.")
            elif user_ans == correct_ans:
                st.success(f"✅ 정답입니다! 정답: **{correct_ans}**")
                score += 1
            else:
                st.error(f"❌ 오답입니다. 선택한 답: **{user_ans}**, 정답: **{correct_ans}**")

            st.markdown("---")

    # 총점 표시 (강조 스타일)
    st.markdown(f"""
    <div style="padding: 1rem; background-color: #f0f2f6; border-radius: 10px; text-align: center;">
        <h3>🎉 최종 점수: {score} / {total}</h3>
    </div>
    """, unsafe_allow_html=True)

    # 🔽 버튼을 결과 박스와 살짝 띄우기
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    # 다시 풀기 버튼
    if st.button("🔄 퀴즈 다시 풀기"):
        st.session_state.pop("quiz_data", None)
        st.session_state.pop("quiz_ready", None)
        st.experimental_rerun()





# 퀴즈 파싱 로직
def parse_question_block(text):
    try:
        question_match = re.search(r"Question\s*\d*:\s*(.*)", text)
        question_raw = question_match.group(1).strip() if question_match else "No question found"
        end_idx = min([(question_raw.find(c) if question_raw.find(c) != -1 else float('inf')) for c in [".", "?", "!"]])
        question = question_raw[:end_idx + 1].strip() if end_idx != float('inf') else question_raw.strip()
        if "___" not in question:
            return None
        options, correct_index = extract_options(text)
        return {"question": question, "options": options, "answer": correct_index}
    except Exception as e:
        print("Parsing error:", e)
        return None

def extract_options(text):
    options = []
    correct_index = None
    for i, letter in enumerate(["A", "B", "C", "D"]):
        match = re.search(rf"{letter}\)\s*(.*)", text)
        if match:
            choice = match.group(1).strip()
            if "✅" in choice:
                correct_index = i
                choice = choice.replace("✅", "").strip()
            options.append(choice)
        else:
            options.append(f"Missing option {letter}")
    return options, correct_index if correct_index is not None else 0

# 메인 실행
def main():
    llm = setup_environment()  # 환경 설정 및 LLM 초기화
    quiz_chain = setup_quiz_chain(llm)  # 퀴즈 체인 설정

    sentences = upload_and_process_file()  # 파일 업로드 및 문장 추출

    # 슬라이더를 이용하여 문제의 수를 사용자에게 입력받습니다.
    num_questions = st.slider("문제의 수를 선택하세요:", 1, 30, 5)

    # 선택된 문제 수를 표시합니다.
    st.write(f"선택된 문제 수: {num_questions}개")

    if sentences:
        st.session_state.quiz_sentences = sentences
        generate_and_display_quiz(quiz_chain, num_questions)  # 문제 생성 및 표시

    if "quiz_data" in st.session_state and st.session_state.get("quiz_ready", False):
        display_quiz_ui(st.session_state.quiz_data)
        

if __name__ == "__main__":
    main()