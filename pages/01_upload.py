import streamlit as st
from functions import *

video_types = ["mp4", "avi", "mov", "webm"]


def transcribe_youtube_video(url: str) -> None:
    with st.status("Downloading video ...") as state:
        download_youtube_video(url)
        state.update(label="Extract audio from video ...")
        video_id = get_video_id(url)
        extract_audio_from_video(video_id)
        state.update(label="Cut audio in chunks ...")
        cut_audio_in_chunks(video_id)
        state.update(label="Transcribe chunks ...")
        video_dir = get_video_dir(video_id)
        transcribe_chunks(video_dir)
        state.update(label="Done!")


def transcribe_uploaded_video(video) -> None:
    with st.status("Loading video ...") as state:
        video_content = video.read()
        tmp_path = get_tmp_path(video.name)
        with open(tmp_path, "wb") as f:
            f.write(video_content)
        video_id = generate_video_id()
        move_permenent_dir(video.name, video_id)
        state.update(label="Extract audio from video ...")
        extract_audio_from_video(video_id)
        state.update(label="Cut audio in chunks ...")
        cut_audio_in_chunks(video_id)
        state.update(label="Transcribe chunks ...")
        video_dir = get_video_dir(video_id)
        transcribe_chunks(video_dir)
        state.update(label="Done!")


title = "Upload video"
st.set_page_config(
    page_icon="🦜",
    page_title=title,
)
st.title(title)
method = st.selectbox(
    "Choose video upload method", ["via youtube url", "upload from your pc"]
)
if method == "via youtube url":
    url = st.text_input("Input the youtube url here")
    if url:
        transcribe_youtube_video(url)
else:
    video = st.file_uploader("Upload media file", type=video_types)
    if video:
        transcribe_uploaded_video(video)
