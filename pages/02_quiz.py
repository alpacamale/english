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

# ==============================
# 💻 환경 설정
# ==============================
def setup_environment():
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    st.set_page_config(page_title="LangChain Quiz Generator", page_icon="📘")
    st.title("📘 LangChain 기반 영어 빈칸 퀴즈 생성기")
    return ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)

# ==============================
# 🤖 퀴즈 프롬프트 설정
# ==============================
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

# ==============================
# 📄 파일 저장 (캐시 없음)
# ==============================
def save_uploaded_file(uploaded_file):
    file_path = f"./.cache/{uploaded_file.name}"
    os.makedirs(".cache", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path

# ==============================
# 📤 파일 업로드 및 문장 추출
# ==============================
def upload_and_process_file():
    uploaded_file = st.file_uploader("📄 .txt 파일 업로드", type=["txt"])
    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)
        return extract_sentences_cached(file_path)
    return None

# ==============================
# 📑 문장 추출 캐시
# ==============================
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

# ==============================
# 🧠 퀴즈 생성 로직
# ==============================
def generate_and_display_quiz(quiz_chain):
    if st.button("🎯 퀴즈 생성하기"):
        quiz_data = generate_quiz(quiz_chain)
        if len(quiz_data) < 5:
            st.warning(f"⚠️ GPT가 5개의 퀴즈를 만들지 못했어요. {len(quiz_data)}개만 생성되었습니다.")
        display_quiz_ui(quiz_data)

def generate_quiz(quiz_chain):
    quiz_data = []
    sentence_idx = 0
    with st.spinner("🧠 GPT로 퀴즈 생성 중..."):
        while len(quiz_data) < 5 and sentence_idx < len(st.session_state.quiz_sentences):
            s = st.session_state.quiz_sentences[sentence_idx]
            sentence_idx += 1
            result = quiz_chain.run({"sentence": s})
            parsed = parse_question_block(result)
            if parsed:
                parsed["source_sentence"] = s
                quiz_data.append(parsed)
    return quiz_data

# ==============================
# 📊 퀴즈 결과 출력
# ==============================
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
    st.subheader("📊 결과")
    score = 0
    for idx, q in enumerate(quiz_data):
        user_ans = user_answers[idx]
        correct_ans = q["options"][q["answer"]]
        if user_ans == correct_ans:
            st.success(f"Q{idx+1}: 정답입니다! ✅")
            score += 1
        else:
            st.error(f"Q{idx+1}: 오답입니다. 정답은 **{correct_ans}** 입니다.")
    st.info(f"🎉 총 정답 개수: {score} / 5")

# ==============================
# 🔍 퀴즈 파싱 로직
# ==============================
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

# ==============================
# 🚀 메인 실행
# ==============================
def main():
    llm = setup_environment()
    quiz_chain = setup_quiz_chain(llm)
    sentences = upload_and_process_file()

    if sentences:
        st.session_state.quiz_sentences = sentences
        generate_and_display_quiz(quiz_chain)

if __name__ == "__main__":
    main()
