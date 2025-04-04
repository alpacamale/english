import streamlit as st
import os
import openai
import random
from dotenv import load_dotenv
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

# 환경 변수 불러오기
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# LangChain 모델 초기화
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)

st.set_page_config(page_title="LangChain Quiz Generator", page_icon="📘")
st.title("📘 LangChain 기반 영어 빈칸 퀴즈 생성기")

# 퀴즈 생성 프롬프트 템플릿
quiz_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an English teacher."),
    ("human", """
    From the sentence below, make ONE multiple-choice fill-in-the-blank English quiz question.

    Instructions:
    - Replace ONE key word with a blank (___).
    - Provide exactly 4 options: A), B), C), D)
    - Only ONE option should be correct.
    - Mark the correct one with ✅
    - Format exactly like this:

    Question 1: I ___ to school every day.
    A) goes
    B) go ✅
    C) going
    D) gone

    Sentence: {sentence}
    """)

])

quiz_chain = LLMChain(llm=llm, prompt=quiz_prompt)

# 문장 파싱 (정답 인식 포함)
import re
def parse_question_block(text):
    try:
        question_match = re.search(r"Question\s*\d*:\s*(.*)", text)
        question_raw = question_match.group(1).strip() if question_match else "No question found"
        
        # 마침표, 물음표, 느낌표 중 가장 앞에 있는 위치 찾기
        end_idx = min([
            (question_raw.find(c) if question_raw.find(c) != -1 else float('inf'))
            for c in [".", "?", "!"]
        ])
        if end_idx != float('inf'):
            question = question_raw[:end_idx + 1].strip()
        else:
            question = question_raw.strip()

        # ✅ 빈칸(underscore)이 없으면 무시
        if "___" not in question:
            return None

        options = []
        correct_index = None
        option_letters = ['A', 'B', 'C', 'D']
        for i, letter in enumerate(option_letters):
            pattern = rf"{letter}\)\s*(.*)"
            match = re.search(pattern, text)
            if match:
                choice = match.group(1).strip()
                if '✅' in choice:
                    correct_index = i
                    choice = choice.replace('✅', '').strip()
                options.append(choice)
            else:
                options.append(f"Missing option {letter}")

        if correct_index is None:
            correct_index = 0

        return {
            "question": question,
            "options": options,
            "answer": correct_index
        }
    except Exception as e:
        print("Parsing error:", e)
        return None




# 파일 업로드
uploaded_file = st.file_uploader("📄 Upload a .txt file", type=["txt"])
if uploaded_file:
    # 텍스트 저장 및 불러오기
    file_path = f"./.cache/{uploaded_file.name}"
    os.makedirs(".cache", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    loader = TextLoader(file_path)
    documents = loader.load()

    # 문장 분리
    splitter = CharacterTextSplitter(separator=".", chunk_size=200, chunk_overlap=0)
    docs = splitter.split_documents(documents)
    sentences = [doc.page_content.strip() for doc in docs if len(doc.page_content.split()) > 4]

    if len(sentences) < 5:
        st.error("파일에 충분한 문장이 없습니다. 최소 5문장 이상 필요합니다.")
    else:

        # 문장 선택 (처음만)
      # 1. 문장 미리 많이 뽑기 (20개까지)
        if "quiz_sentences" not in st.session_state:
            st.session_state.quiz_sentences = random.sample(sentences, min(20, len(sentences)))

        # 2. 퀴즈 생성 버튼
        if st.button("🎯 퀴즈 생성하기"):
            st.session_state.quiz_data = []
            with st.spinner("GPT로 퀴즈 생성 중..."):
                sentence_idx = 0
                while len(st.session_state.quiz_data) < 5 and sentence_idx < len(st.session_state.quiz_sentences):
                    s = st.session_state.quiz_sentences[sentence_idx]
                    sentence_idx += 1

                    result = quiz_chain.run({"sentence": s})
                    parsed = parse_question_block(result)
                    if parsed:
                        parsed["source_sentence"] = s
                        st.session_state.quiz_data.append(parsed)

            if len(st.session_state.quiz_data) < 5:
                st.warning(f"⚠️ GPT가 5개의 퀴즈를 만들지 못했어요. {len(st.session_state.quiz_data)}개만 생성되었습니다.")






# 퀴즈 UI
if "quiz_data" in st.session_state:
    st.subheader("📝 퀴즈 풀기")
    user_answers = {}
    with st.form("quiz_form"):
        for idx, q in enumerate(st.session_state.quiz_data):
            st.write(f"**Q{idx+1}. {q['question']}**")
            user_answers[idx] = st.radio(
                "선택하세요:",
                q["options"],
                key=f"quiz_{idx}",
                index=None
            )
            st.markdown("---")
        submitted = st.form_submit_button("✅ 제출")

    if submitted:
        st.subheader("📊 결과")
        score = 0
        for idx, q in enumerate(st.session_state.quiz_data):
            user_ans = user_answers[idx]
            correct_ans = q["options"][q["answer"]]
            if user_ans == correct_ans:
                st.success(f"Q{idx+1}: 정답입니다!")
                score += 1
            else:
                st.error(f"Q{idx+1}: 오답입니다. 정답: **{correct_ans}**")
        st.info(f"🎉 총 {score} / 5 문제 정답!")
