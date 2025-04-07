# SESAC mini project

STT와 OpenAI Whisper API를 이용한 AI 언어 학습 프로그램

## Summary

여기를 채워줘

## Period

2025.04.02 ~ 2025.04.08

## Team

[원예은](https://github.com/yetk124), [박병준](https://github.com/alpacamale), [박지윤](#)

## Upload Page

유저에게 youtube url 혹은 PC로부터 영상을 업로드 받고, Openai Whisper API를 이용해서 Speech-to-Text 기술을 이용해서 vtt 파일을 생성합니다.

## Shadowing Page

쉐도잉을 돕는 프로그램입니다. 다음과 같은 기능을 제공합니다:

- Upload Page에서 생성한 스크립트를 화면에 표시하고, 대사를 클릭했을 때, 해당 구간의 영상이 재생됩니다.
- 사용자의 음성을 텍스트로 변환한 후, 비디오의 스크립트와 비교합니다.
- STT로 인식한 사용자의 음성과 스크립트의 일치하는 정도를 퍼센트(%)로 확인하고, 실제로 생성된 텍스트를 비교할 수 있습니다.

향후 발전 방향

OpenSMILE 을 이용해서 억양, 피치, 발성 속도 등을 분석하여 개인 코칭이 가능하도록 해야함.

## English Quiz Page

음성 인식과 AI 자연어 처리 기술을 활용한 인터랙티브 언어 학습 플랫폼으로, 사용자의 음성 입력을 텍스트로 변환하고 객관식 퀴즈를 통해 언어 이해력과 어휘력을 향상시킵니다.

OpenAI GPT 모델을 활용해 **영어 빈칸 사지선다형 퀴즈 5문제**를 자동 생성하는 웹 애플리케이션입니다.

## 설치 방법

```
# 가상 환경 생성
pyenv local 3.12.2
python -m venv env
source env/bin/activate

# 필수 패키지 설치
pip install -r requirements.txt
```

## 환경 변수

OpenAI API 키가 필요합니다. `.env` 또는 환경변수로 설정하세요:

```
export OPENAI_API_KEY='your-api-key'
```

## ffmpeg

[ffmpeg 패키지](https://www.ffmpeg.org/)를 설치해야 합니다.

```
# arch linux
sudo pacman -S ffmpeg
```

## 실행 방법

```
streamlit run Home.py
```

## 프로젝트 회고

### 잘한 점

- API의 비용을 아끼기 위해 분할한 Audio chunk를 전부 whisper api에 보내지 않고, 첫 한개나 두개 청크만 이용해서 비용을 많이 아꼇다.
- 스트림릿의 캐쉬와 파일 기반 구조로 이미 완료한 코드를 다시 돌리지 않아서 API 비용과 리소스를 많이 아꼈다.
- 처음부터 pyenv를 이용해서 파이썬 버전을 맞추고 시작했기 때문에 각자 다른 환경에서 일어날 수 있는 충돌을 없엤다.
- ChatGPT가 스트림릿은 자바스크립트 없이 비디오 제어가 불가능하고, 스크롤 가능한 컴포넌트가 없다고 했지만, 포기하지 않고 구글링하고, 여러 시도를 하며 답을 찾았다.

### 아쉬운 점

- 개발 기간이 주말을 제외하고, 주어진 시간이 적었던 첫 날을 제외하면 3일정도밖에 안되어서 더 완성된 서비스를 만들지 못했다.
- 디렉토리 구조를 처음부터 세밀하게 설계하지 않아서 나중에 리펙토링할때 시간을 더 쏟았다.
