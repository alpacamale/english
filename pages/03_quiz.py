# 🎯 영상 선택 → 자막 기반 영어 퀴즈 생성기

import streamlit as st
import os
import openai
import random
import re
import pyttsx3
from dotenv import load_dotenv
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from functions import (
    get_video_ids, get_video_names,
    get_video_name_map, get_base_dir,
    get_audio_transcript_path,
)


# ✅ 파일 경로 내 특수문자 제거
def change_path(path: str) -> str:
    return re.sub(r'[<>:"/\\|?*&=]', '_', path)


# ✅ LLM 환경 설정 및 모델 로딩
def setup_environment():
    load_dotenv()
    st.set_page_config(page_title="Video Quiz Generator", page_icon="🎬")
    st.title("🎬 영상 자막 기반 영어 퀴즈 생성기")
    return ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)


# ✅ 퀴즈 생성용 프롬프트 체인 설정
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

Format:

Question 1: I ____ to school every day.
A) goes
B) go ✅
C) going
D) gone

Sentence: {sentence}
""")
    ])
    return LLMChain(llm=llm, prompt=quiz_prompt)


# ✅ 자막 파일 로딩 및 문장 추출 (캐시 포함)
@st.cache_resource(show_spinner="📚 문장 추출 중...")
def extract_sentences_cached(file_path):
    return extract_sentences(file_path)

def extract_sentences(file_path):
    loader = TextLoader(file_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(separators=[".", "!", "?"], chunk_size=200)
    docs = splitter.split_documents(documents)
    # 최소 5단어 이상 문장만 필터링
    sentences = [doc.page_content.strip() for doc in docs if len(doc.page_content.split()) > 4]
    return random.sample(sentences, min(20, len(sentences)))


# ✅ 문장 리스트를 기반으로 퀴즈 생성
def generate_quiz(quiz_chain, sentences, num_questions):
    quiz_data = []
    sentence_idx, attempts = 0, 0

    with st.spinner("❔❕ GPT로 퀴즈 생성 중..."):
        while len(quiz_data) < num_questions and attempts < num_questions * 3:
            if sentence_idx >= len(sentences):
                sentence_idx = 0
            s = sentences[sentence_idx]
            sentence_idx += 1

            result = quiz_chain.run({"sentence": s})
            parsed = parse_question_block(result)
            if parsed:
                parsed["source_sentence"] = s
                quiz_data.append(parsed)
            attempts += 1

    return quiz_data


# ✅ 퀴즈 UI 출력
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
        show_results(quiz_data, user_answers)


# ✅ 정답 채점 및 결과 출력
def show_results(quiz_data, user_answers):
    st.markdown("📊 채점 결과")
    score = 0

    for idx, q in enumerate(quiz_data):
        user_ans = user_answers.get(idx)
        correct_ans = q["options"][q["answer"]]

        with st.container():
            st.markdown(f"**Q{idx + 1}. {q['question']}**")
            if user_ans == correct_ans:
                st.success(f"✅ 정답입니다! **{correct_ans}**")
                score += 1
            else:
                st.error(f"❌ 오답입니다. 선택: **{user_ans}**, 정답: **{correct_ans}**")
        st.markdown("---")

    st.info(f"🎉 최종 점수: {score} / {len(quiz_data)}")


# ✅ GPT 응답 파싱 → 퀴즈 형식으로
def parse_question_block(text):
    try:
        match = re.search(r"Question\s*\d*:\s*(.*)", text)
        question_raw = match.group(1).strip() if match else "No question"

        if "___" not in question_raw:
            return None

        # 문장 끝 부호 기준으로 질문 부분만 추출
        end_idx = min([question_raw.find(c) if c in question_raw else float("inf") for c in [".", "!", "?"]])
        question = question_raw[:end_idx + 1] if end_idx != float("inf") else question_raw

        options, correct_idx = extract_options(text)
        return {"question": question.strip(), "options": options, "answer": correct_idx}
    except Exception as e:
        print("Parsing Error:", e)
        return None


# ✅ 보기 옵션 추출 및 정답 인덱스 탐지
def extract_options(text):
    options, correct_index = [], None
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


# ✅ Streamlit 메인 실행
def main():
    llm = setup_environment()
    quiz_chain = setup_quiz_chain(llm)

    video_ids = get_video_ids()
    video_names = get_video_names(video_ids)
    video_name_map = get_video_name_map(video_ids)

    if not video_names:
        st.warning("🎞 먼저 영상을 업로드하세요!")
        return

    selected_video = st.selectbox("🎥 퀴즈를 풀 영상 선택", video_names)
    video_id = video_name_map[selected_video]
    base_dir = get_base_dir(video_id)
    transcript_path = get_audio_transcript_path(base_dir)

    try:
        sentences = extract_sentences_cached(transcript_path)
    except Exception as e:
        st.error(f"❌ 자막 파일을 불러오는 중 오류 발생: {e}")
        return

    if len(sentences) < 5:
        st.error("해당 영상 자막에서 충분한 문장을 찾을 수 없습니다.")
        return

    num_questions = st.slider("퀴즈 문제 수", 1, 20, 5)
    st.write(f"총 {num_questions}문제를 생성합니다.")

    if st.button("🧩 퀴즈 만들기"):
        quiz_data = generate_quiz(quiz_chain, sentences, num_questions)
        if quiz_data:
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_ready = True
        else:
            st.session_state.quiz_ready = False
            st.error("퀴즈를 생성하지 못했습니다.")

    # ✅ 퀴즈가 준비된 경우에만 출력 (여기서만 출력!)
    if st.session_state.get("quiz_ready", False):
        display_quiz_ui(st.session_state.quiz_data)



if __name__ == "__main__":
    main()
