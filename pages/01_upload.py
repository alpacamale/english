import streamlit as st
from functions import *

video_types = ["mp4", "avi", "mov", "webm"]


def transcribe_youtube_video(url: str) -> None:
    with st.status("Downloading video ...") as state:
        download_youtube_video(url)

        state.update(label="Extract audio from video ...")
        video_id = get_video_id(url)
        base_dir = get_base_dir(video_id)
        extract_audio_from_video(base_dir)

        state.update(label="Cut audio in chunks ...")
        source = get_audio_path(base_dir)
        chunks_dir = get_audio_chunk_dir(base_dir)
        cut_audio_in_chunks(source, chunks_dir)

        state.update(label="Transcribe chunks ...")
        destination = get_audio_transcript_path(base_dir)
        transcribe_chunks(base_dir, chunks_dir, destination)

        state.update(label="Done!")


def transcribe_uploaded_video(video) -> None:
    with st.status("Loading video ...") as state:
        video_content = video.read()
        tmp_path = get_tmp_path(video.name)
        with open(tmp_path, "wb") as f:
            f.write(video_content)
        video_id = generate_video_id()
        move_to_permenent_dir(video.name, video_id)

        state.update(label="Extract audio from video ...")
        base_dir = get_base_dir(video_id)
        extract_audio_from_video(base_dir)

        state.update(label="Cut audio in chunks ...")
        source = get_audio_path(base_dir)
        destination = get_audio_chunk_dir(base_dir)
        cut_audio_in_chunks(source, destination)

        state.update(label="Transcribe chunks ...")
        chunks_dir = get_audio_chunk_dir(base_dir)
        destination = get_audio_transcript_path(base_dir)
        transcribe_chunks(base_dir, chunks_dir, destination)

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
