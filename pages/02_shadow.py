import streamlit as st
from functions import *
from langchain.document_loaders import TextLoader


@st.cache_data(show_spinner="Loading text ...")
def load_text(base_dir: str) -> list[dict]:
    transcript_path = get_audio_transcript_path(base_dir)
    loader = TextLoader(transcript_path)
    docs = loader.load()
    text = docs[0].page_content
    parser = VttTimestampOutputParser()
    return parser.parse(text)


def select_video(video_ids: list[str]) -> tuple[str, str]:
    """
    Return video metadata

    Returns:
        - base_dir (str): The directory path where the video is stored
        - video_path (str): The file path to the video
    """
    video_names = get_video_names(video_ids)
    video_name_map = get_video_name_map(video_ids)
    video_name = st.selectbox("Select a video you want to see", video_names)
    if video_name != st.session_state["video_name"]:
        st.session_state.update(
            {
                "start_time": 0,
                "end_time": None,
                "loop": False,
                "record": False,
                "video_name": video_name,
                "transcribe": False,
                "score": False,
            }
        )
    video_id = video_name_map[video_name]
    base_dir = get_base_dir(video_id)
    video_path = get_video_path(base_dir)
    return base_dir, video_path


def transcribe_echo_voice(wav_audio_data, base_dir):
    with st.status("Loading audio ...") as state:
        wav_bytes = wav_audio_data.read()
        echo_voice_path = get_echo_voice_path(base_dir)
        with open(echo_voice_path, "wb") as voice:
            voice.write(wav_bytes)

        state.update(label="Splitting audio in chunks ...")
        chunks_dir = get_echo_chunk_dir(base_dir)
        cut_audio_in_chunks(echo_voice_path, chunks_dir)

        state.update(label="Transcribing audio chunks ...")
        destination = get_echo_transcript_path(base_dir)
        transcribe_chunks(base_dir, chunks_dir, destination)

        state.update(label="Done!")


def get_shadow_result(base_dir: str) -> str:
    with st.status("Transcribeing speech to text ...") as state:
        audio_dialog, echo_dialog = get_dialog(base_dir)
        state.update(label="Compare each speeches ...")
        correction_rate = get_correction_rate(audio_dialog, echo_dialog)
        state.update(label="Done!")
    return f"Your speech accuracy: {correction_rate}%", audio_dialog, echo_dialog


title = "Mocking bird"
st.set_page_config(
    page_icon="🦜",
    page_title=title,
)

if "initial" not in st.session_state:
    st.session_state.update(
        {
            "initial": True,
            "start_time": 0,
            "end_time": None,
            "loop": False,
            "caption": True,
            "record": False,
            "video_name": None,
            "transcribe": False,
        }
    )

video_ids = get_video_ids()
if get_video_names(video_ids) == []:
    st.write("### You need to upload the video first!")
else:
    base_dir, video_path = select_video(video_ids)

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
            captions = load_text(base_dir)
            for caption in captions:
                button = st.button(caption["text"], key=caption["start"])
                if button:
                    st.session_state["start_time"] = caption["start"]
                    st.session_state["end_time"] = caption["end"]
                    st.rerun()

    if record:
        wav_audio_data = st.audio_input("Record your voice!")
        if wav_audio_data is not None:
            if st.session_state["transcribe"] == False:
                button = st.button("Transcribe It!")
                if button:
                    st.session_state["transcribe"] = True
                    transcribe_echo_voice(wav_audio_data, base_dir)
                    st.rerun()
            elif st.session_state["score"] == False:
                score_button = st.button(
                    "Recording complete! Check your score!", key="score_button"
                )
                if score_button:
                    st.session_state["score"] = True
            else:
                result, audio_dialog, echo_dialog = get_shadow_result(base_dir)
                st.warning(result)
                with st.expander("Compare dialog!") as expand:
                    audio_transcript_column, echo_transcript_column = st.columns(2)
                    with audio_transcript_column:
                        st.write("Original video transcript")
                        audio_script = dialog_to_text(audio_dialog)
                        with st.container(height=300):
                            st.write(audio_script)
                    with echo_transcript_column:
                        st.write("Your voice transcript")
                        echo_script = dialog_to_text(echo_dialog)
                        with st.container(height=300):
                            st.write(echo_script)
                again_button = st.button(
                    "Re-record your voice and try for a better score!"
                )
                if again_button:
                    st.session_state.update(
                        {
                            "transcribe": False,
                            "score": False,
                        }
                    )
