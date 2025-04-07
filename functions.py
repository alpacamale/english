import subprocess
import os
from glob import glob
from pydub import AudioSegment
import math
from tqdm import tqdm
import openai
from langchain.schema.output_parser import BaseOutputParser
from datetime import timedelta
import json
import secrets
from langchain.document_loaders import TextLoader
from jiwer import wer
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import re


def initial_server() -> None:
    os.makedirs("files", exist_ok=True)
    os.makedirs(".cache", exist_ok=True)


def get_video_id(url: str) -> str:
    return url.lstrip("https://www.youtube.com/watch?v=")


def get_base_dir(video_id: str) -> str:
    return f"files/{video_id}"


def get_video_path(base_dir: str) -> str:
    extensions = ["mp4", "avi", "mov", "webm"]
    files = glob(f"{base_dir}/media/*.*")
    return next((file for file in files if file.split(".")[-1] in extensions), None)


def get_audio_path(base_dir: str) -> str:
    return f"{base_dir}/media/audio.mp3"


# def get_chunk_dir(base_dir: str) -> str:
#     return f"{base_dir}/media/chunks"


def get_audio_chunk_dir(base_dir: str) -> str:
    return f"{base_dir}/media/chunks/audio"


def get_echo_chunk_dir(base_dir: str) -> str:
    return f"{base_dir}/media/chunks/echo"


def get_audio_transcript_path(base_dir: str) -> str:
    return f"{base_dir}/audio_transcript.txt"


def get_echo_transcript_path(base_dir: str) -> str:
    return f"{base_dir}/echo_transcript.txt"


def get_metadata_path(base_dir: str) -> str:
    return f"{base_dir}/meta.json"


def get_video_name(video_id: str) -> str:
    base_dir = get_base_dir(video_id)
    metadata_path = get_metadata_path(base_dir)
    with open(metadata_path, "r") as f:
        result = json.loads(f.read())
    return result["title"]


def get_video_ids() -> list[str]:
    return [video_path.lstrip("files/") for video_path in glob("files/*")]


def get_video_name_map(video_ids: list[str]) -> dict:
    return {get_video_name(video_id): video_id for video_id in video_ids}


def get_video_names(video_ids: list[str]) -> list[str]:
    return [get_video_name(video_id) for video_id in video_ids]


def get_tmp_path(video_name) -> str:
    return f"./.cache/{video_name}"


def get_echo_voice_path(base_dir: str) -> str:
    return f"{base_dir}/media/echo.wav"


def download_youtube_video(url: str) -> None:
    video_id = get_video_id(url)
    base_dir = get_base_dir(video_id)
    if not os.path.exists(base_dir):
        command = ["yt-dlp", "-o", f"{base_dir}/media/video.webm", url]
        subprocess.run(command)
        metadata_path = get_metadata_path(base_dir)
        command = ["yt-dlp", "--get-title", url]
        title = subprocess.run(
            command, stdout=subprocess.PIPE, text=True
        ).stdout.strip()
        with open(metadata_path, "w") as f:
            metadata = json.dumps({"title": title})
            f.write(metadata)


def extract_audio_from_video(base_dir: str) -> None:
    video_path = get_video_path(base_dir)
    audio_path = get_audio_path(base_dir)
    if not os.path.exists(audio_path):
        command = ["ffmpeg", "-i", video_path, "-vn", audio_path]
        subprocess.run(command)


def cut_audio_in_chunks(source: str, destination: str, chunk_size: int = 10) -> None:
    os.makedirs(destination, exist_ok=True)
    track = AudioSegment.from_mp3(source)
    chunk_len = chunk_size * 60 * 1000
    chunks = math.ceil(len(track) / chunk_len)

    for i in tqdm(range(chunks), "Split audio file into chunks"):
        start_time = i * chunk_len
        end_time = (i + 1) * chunk_len
        chunk = track[start_time:end_time]
        chunk.export(f"{destination}/chunk_{i}.mp3", format="mp3")


def transcribe_chunks(base_dir: str, chunks_dir: str, destination: str) -> None:
    if not os.path.exists(destination):
        files = glob(f"{chunks_dir}/*")
        for file in tqdm(files, "Transcribing audio chunks"):
            with open(file, "rb") as audio_file, open(destination, "a") as text_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="vtt",
                    language="en",
                )
                text_file.write(transcript)


def parse_timestamp(ts: str) -> timedelta:
    hours, minutes, rest = ts.split(":")
    seconds, milliseconds = rest.split(".")
    return timedelta(
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds),
        milliseconds=int(milliseconds),
    )


class VttTimestampOutputParser(BaseOutputParser):
    def parse(self, text: str) -> list[dict]:
        lines = text.strip().splitlines()
        result = []
        offset = timedelta(minutes=0)
        for i, line in enumerate(lines):
            if "-->" in line:
                start, end = line.split(" --> ")
                caption = lines[i + 1] if i + 1 < len(lines) else ""
                result.append(
                    {
                        "start": parse_timestamp(start.strip()) + offset,
                        "end": parse_timestamp(end.strip()) + offset,
                        "text": caption.strip(),
                    }
                )
            elif "WEBVTT" in line and i != 0:
                offset += parse_timestamp(end.strip())
        return result


class VttOutputParser(BaseOutputParser):
    def parse(self, text: str) -> list[dict]:
        lines = text.strip().splitlines()
        result = []
        for i, line in enumerate(lines):
            if "-->" in line:
                caption = lines[i + 1] if i + 1 < len(lines) else ""
                result.append(caption)
        return " ".join(result)


def generate_video_id(length: int = 11) -> str:
    token = secrets.token_urlsafe(8)
    return token[:length]


def move_to_permenent_dir(video_name: str, base_dir: str) -> None:
    tmp_path = get_tmp_path(video_name)
    os.makedirs(base_dir, exist_ok=True)
    title, ext = video_name.split(".")
    video_path = f"{base_dir}/video.{ext}"
    if not os.path.exists(video_path):
        command = ["mv", tmp_path, video_path]
        subprocess.run(command)
        with open(f"{base_dir}/meta.json", "w") as f:
            metadata = json.dumps({"title": title})
            f.write(metadata)


def get_dialog(base_dir: str) -> tuple[str, str]:
    audio_path = get_audio_transcript_path(base_dir)
    echo_path = get_echo_transcript_path(base_dir)

    audio_loader = TextLoader(audio_path)
    echo_loader = TextLoader(echo_path)
    audio_docs = audio_loader.load()
    echo_docs = echo_loader.load()
    audio_text = audio_docs[0].page_content
    echo_text = echo_docs[0].page_content

    parser = VttOutputParser()
    audio_dialog = re.sub(r"[.!?,]", "", parser.parse(audio_text).lower())
    echo_dialog = re.sub(r"[.!?,]", "", parser.parse(echo_text).lower())

    llm = ChatOpenAI(temperature=0.1, model="gpt-4o-mini")
    prompt = PromptTemplate.from_template(
        """
        You will receive two texts: the original script and the shadowed version spoken by a learner.

        Your task is to split both texts into lists of sentences and align them positionally.

        Important constraints:
        - The two lists **must be exactly the same length**, as they will be compared using Word Error Rate (WER).
        - If a sentence from the original script is missing or skipped in the shadowed version, insert an empty string ("") at the correct position in the shadow list.
        - Do not merge, rephrase, or split sentences arbitrarily. Keep the original sentences exactly as they are.
        - Maintain the order of the original script.

        Return only valid JSON with the following format:
        {{
        "original_sentences": [ ... ],
        "shadow_sentences": [ ... ]
        }}

        Do not include any explanations, markdown, or code blocks—return only the raw JSON.

        Original script:
        {audio}

        Shadowed version:
        {echo}
        """
    )
    chain = prompt | llm
    response = chain.invoke({"audio": audio_dialog, "echo": echo_dialog})
    result = json.loads(response.content)
    return result["original_sentences"], result["shadow_sentences"]


def dialog_to_text(dialog: list[str]) -> str:
    return "\n".join(dialog)


def get_correction_rate(audio_dialog: list[str], echo_dialog: list[str]) -> str:
    correction_rates = []
    for ref, hyp in zip(audio_dialog, echo_dialog):
        correction_rates.append(1.0 - wer(ref, hyp))
    return f"{sum(correction_rates) / len(correction_rates):.2%}"
