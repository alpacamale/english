import streamlit as st
from functions import *
from langchain.document_loaders import TextLoader
from datetime import datetime


video_id = "QHrUGYqxj4E"
video_dir = get_video_dir(video_id)
video_path = get_video_path(video_dir)
start = datetime.now()


@st.cache_data(show_spinner="Loading text ...")
def load_text(video_id):
    video_dir = get_video_dir(video_id)
    transcript_path = get_transcript_path(video_dir)
    loader = TextLoader(transcript_path)
    docs = loader.load()
    parser = VttTimestampOutputParser()
    text = docs[0].page_content
    return parser.parse(text)


if "initial" not in st.session_state:
    st.session_state["initial"] = True
    st.session_state["start_time"] = 0
    st.session_state["end_time"] = None
    st.session_state["loop"] = False

title = "Mocking bird"
st.set_page_config(
    page_icon="🦜",
    page_title=title,
)
st.title(title)
st.video(
    video_path,
    start_time=st.session_state["start_time"],
    end_time=st.session_state["end_time"] if st.session_state["loop"] else None,
    loop=st.session_state["loop"],
)

captions = load_text(video_id)

repeat = st.toggle(
    "repeat",
    st.session_state["loop"],
)
if repeat != st.session_state["loop"]:
    st.session_state["loop"] = repeat
    st.rerun()

with st.container(border=True, height=200):
    for caption in captions:
        button = st.button(caption["text"], key=caption["start"])
        if button:
            st.session_state["start_time"] = caption["start"]
            st.session_state["end_time"] = caption["end"]
            st.rerun()
