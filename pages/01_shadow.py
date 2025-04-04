import streamlit as st
from functions import *
from langchain.document_loaders import TextLoader
from datetime import datetime


video_id = "MS5UjNKw_1M"
video_dir = get_video_dir(video_id)
video_path = get_video_path(video_dir)


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
    st.session_state.update(
        {
            "initial": True,
            "start_time": 0,
            "end_time": None,
            "loop": False,
            "caption": True,
            "record": False,
        }
    )

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

repeat_column, caption_column, record_column = st.columns(3)
with repeat_column:
    repeat = st.toggle("repeat", st.session_state["loop"], key="repeat_toggle")
with caption_column:
    caption = st.toggle("caption", True, key="caption_toggle")
with record_column:
    record = st.toggle("record voice", False, key="record_toggle")

if repeat != st.session_state["loop"]:
    st.session_state["loop"] = repeat
    st.rerun()

if caption:
    with st.container(border=True, height=200):
        captions = load_text(video_id)
        for caption in captions:
            button = st.button(caption["text"], key=caption["start"])
            if button:
                st.session_state["start_time"] = caption["start"]
                st.session_state["end_time"] = caption["end"]
                st.rerun()
