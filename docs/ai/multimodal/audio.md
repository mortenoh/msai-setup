# Audio Processing

Local audio processing for speech-to-text, text-to-speech, and audio analysis.

## Speech-to-Text (Whisper)

### Local Whisper with Python

```bash
pip install openai-whisper
```

```python
import whisper

# Load model
model = whisper.load_model("base")  # tiny, base, small, medium, large

# Transcribe
result = model.transcribe("audio.mp3")
print(result["text"])
```

### Whisper Model Sizes

| Model | Size | VRAM | Speed | Quality |
|-------|------|------|-------|---------|
| tiny | 39M | ~1GB | Fastest | Basic |
| base | 74M | ~1GB | Fast | Good |
| small | 244M | ~2GB | Medium | Better |
| medium | 769M | ~5GB | Slow | High |
| large-v3 | 1.5G | ~10GB | Slowest | Best |

### Faster Whisper

Optimized implementation using CTranslate2:

```bash
pip install faster-whisper
```

```python
from faster_whisper import WhisperModel

# Load model (uses less VRAM, faster)
model = WhisperModel("base", device="cuda", compute_type="float16")

# Transcribe
segments, info = model.transcribe("audio.mp3")

print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

### With LocalAI

```yaml
# docker-compose.yml
services:
  localai:
    image: localai/localai:latest-gpu-nvidia-cuda-12
    ports:
      - "8080:8080"
    volumes:
      - ./models:/build/models
    environment:
      - WHISPER_MODEL=base
```

```python
import requests

def transcribe_localai(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        response = requests.post(
            "http://localhost:8080/v1/audio/transcriptions",
            files={"file": f},
            data={"model": "whisper-1"}
        )
    return response.json()["text"]
```

## Text-to-Speech (TTS)

### Coqui TTS

```bash
pip install TTS
```

```python
from TTS.api import TTS

# List available models
print(TTS().list_models())

# Load model
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")

# Generate speech
tts.tts_to_file(
    text="Hello, this is a test of local text to speech.",
    file_path="output.wav"
)
```

### Piper TTS (Fast)

```bash
pip install piper-tts
```

```python
import subprocess

def piper_tts(text: str, output_path: str, voice: str = "en_US-lessac-medium"):
    """Generate speech with Piper."""
    subprocess.run([
        "piper",
        "--model", voice,
        "--output_file", output_path
    ], input=text.encode(), check=True)

piper_tts("Hello world", "output.wav")
```

### With LocalAI

```python
def text_to_speech(text: str, output_path: str):
    response = requests.post(
        "http://localhost:8080/v1/audio/speech",
        json={
            "input": text,
            "model": "tts-1",
            "voice": "alloy"
        }
    )

    with open(output_path, "wb") as f:
        f.write(response.content)
```

### Kokoro TTS

High-quality local TTS with an 82M parameter model. Apache-2.0 license, 54+ voices across 10+ languages (English, Spanish, French, German, Italian, Portuguese, Hindi, Japanese, Korean, Chinese). Supports voice blending, ONNX runtime for fast CPU inference, and PyTorch GPU acceleration.

#### TTS Options Comparison

| Engine | Parameters | Voices | Languages | API | License |
|--------|-----------|--------|-----------|-----|---------|
| Coqui TTS | Varies | Many | 20+ | Python | MPL-2.0 |
| Piper | Small | 100+ | 30+ | CLI | MIT |
| Bark | 300M+ | Limited | 10+ | Python | MIT |
| **Kokoro** | **82M** | **54+** | **10+** | **OpenAI-compatible** | **Apache-2.0** |

#### Python (pip)

```bash
pip install kokoro
```

```python
from kokoro import KPipeline

# Initialize pipeline (language code: 'a' for American English)
pipeline = KPipeline(lang_code="a")

# Generate speech
generator = pipeline("Hello, this is Kokoro text to speech.", voice="af_heart")

for i, (gs, ps, audio) in enumerate(generator):
    # Save audio (24kHz sample rate)
    import soundfile as sf
    sf.write(f"output_{i}.wav", audio, 24000)
```

Available language codes:

| Code | Language | Code | Language |
|------|----------|------|----------|
| `a` | American English | `b` | British English |
| `e` | Spanish | `f` | French |
| `h` | Hindi | `i` | Italian |
| `j` | Japanese | `k` | Korean |
| `p` | Brazilian Portuguese | `z` | Chinese |

#### Docker (Kokoro-FastAPI)

OpenAI-compatible TTS server using the Kokoro model:

```yaml
# docker-compose.yml
services:
  kokoro:
    image: ghcr.io/remsky/kokoro-fastapi:v0.4-gpu
    ports:
      - "8880:8880"
    volumes:
      - kokoro-voices:/app/api/src/voices
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  kokoro-voices:
```

For CPU-only deployment:

```yaml
services:
  kokoro:
    image: ghcr.io/remsky/kokoro-fastapi:v0.4-cpu
    ports:
      - "8880:8880"
    volumes:
      - kokoro-voices:/app/api/src/voices

volumes:
  kokoro-voices:
```

Generate speech using the OpenAI-compatible API:

```bash
curl -X POST http://localhost:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kokoro",
    "input": "Hello, this is a test of Kokoro TTS.",
    "voice": "af_heart",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8880/v1", api_key="not-needed")

response = client.audio.speech.create(
    model="kokoro",
    input="Hello from Kokoro TTS!",
    voice="af_heart",
    response_format="mp3",
)

response.stream_to_file("output.mp3")
```

!!! note "AMD ROCm support"
    Kokoro-FastAPI has a PR (#431) adding gfx1151 (Strix Halo) ROCm support. Until merged,
    use the CPU image with ONNX runtime -- inference is fast even on CPU due to the small
    model size (82M parameters).

#### Voice Blending

Kokoro supports blending two voices to create custom voice profiles:

```bash
# Blend two voices (70% af_heart, 30% af_nova)
curl -X POST http://localhost:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kokoro",
    "input": "This is a blended voice.",
    "voice": "af_heart(0.7)+af_nova(0.3)"
  }' \
  --output blended.mp3
```

#### Integration with Open WebUI

Configure Kokoro as the TTS provider in Open WebUI:

1. Go to **Admin Panel** > **Settings** > **Audio**
2. Set **TTS Engine** to `OpenAI`
3. Set **API Base URL** to `http://kokoro:8880/v1` (Docker) or `http://localhost:8880/v1`
4. Set **API Key** to any value (not validated)
5. Set **TTS Model** to `kokoro`
6. Set **TTS Voice** to `af_heart` (or any available voice)

## Audio Transcription Pipeline

### Basic Pipeline

```python
from faster_whisper import WhisperModel
from pathlib import Path

class AudioTranscriber:
    def __init__(self, model_size: str = "base"):
        self.model = WhisperModel(model_size, device="cuda", compute_type="float16")

    def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio file."""
        segments, info = self.model.transcribe(audio_path)

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": [
                {
                    "start": s.start,
                    "end": s.end,
                    "text": s.text.strip()
                }
                for s in segments
            ],
            "text": " ".join(s.text.strip() for s in segments)
        }

    def transcribe_with_timestamps(self, audio_path: str) -> str:
        """Transcribe with timestamps."""
        result = self.transcribe(audio_path)

        lines = []
        for seg in result["segments"]:
            timestamp = f"[{seg['start']:.2f} - {seg['end']:.2f}]"
            lines.append(f"{timestamp} {seg['text']}")

        return "\n".join(lines)

# Usage
transcriber = AudioTranscriber()
result = transcriber.transcribe("meeting.mp3")
print(result["text"])
```

### Batch Transcription

```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def batch_transcribe(audio_dir: str, output_dir: str):
    """Transcribe all audio files in a directory."""
    transcriber = AudioTranscriber()
    audio_files = list(Path(audio_dir).glob("*.mp3")) + list(Path(audio_dir).glob("*.wav"))

    Path(output_dir).mkdir(exist_ok=True)

    for audio_path in audio_files:
        print(f"Transcribing: {audio_path.name}")
        result = transcriber.transcribe(str(audio_path))

        output_path = Path(output_dir) / f"{audio_path.stem}.txt"
        output_path.write_text(result["text"])

batch_transcribe("./recordings", "./transcripts")
```

## Voice Cloning

### Coqui XTTS

```python
from TTS.api import TTS

# Load XTTS model
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

# Clone voice from sample
tts.tts_to_file(
    text="Hello, this is my cloned voice.",
    file_path="cloned_output.wav",
    speaker_wav="voice_sample.wav",  # Reference audio
    language="en"
)
```

## Audio Analysis with LLM

```python
def analyze_transcript(transcript: str) -> str:
    """Analyze a transcript with an LLM."""
    import ollama

    response = ollama.chat(
        model="llama3.2",
        messages=[{
            "role": "user",
            "content": f"""Analyze this transcript and provide:
1. Main topics discussed
2. Key points and takeaways
3. Action items mentioned
4. Sentiment analysis

Transcript:
{transcript}"""
        }]
    )

    return response["message"]["content"]

# Usage
transcriber = AudioTranscriber()
result = transcriber.transcribe("meeting.mp3")
analysis = analyze_transcript(result["text"])
print(analysis)
```

## Real-Time Transcription

```python
import pyaudio
import numpy as np
from faster_whisper import WhisperModel

class RealtimeTranscriber:
    def __init__(self):
        self.model = WhisperModel("tiny", device="cuda", compute_type="float16")
        self.audio = pyaudio.PyAudio()
        self.sample_rate = 16000
        self.chunk_duration = 5  # seconds

    def transcribe_stream(self):
        """Transcribe from microphone in real-time."""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.sample_rate * self.chunk_duration
        )

        print("Listening... (Ctrl+C to stop)")

        try:
            while True:
                # Read audio chunk
                data = stream.read(self.sample_rate * self.chunk_duration)
                audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                # Transcribe
                segments, _ = self.model.transcribe(audio_array)

                for segment in segments:
                    print(segment.text, end=" ", flush=True)

        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            stream.close()

# Usage
# transcriber = RealtimeTranscriber()
# transcriber.transcribe_stream()
```

## Audio Format Conversion

```python
import subprocess

def convert_audio(input_path: str, output_path: str, sample_rate: int = 16000):
    """Convert audio to WAV format suitable for Whisper."""
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", str(sample_rate),
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_path
    ], check=True, capture_output=True)

# Convert before transcribing
convert_audio("video.mp4", "audio.wav")
```

## Speaker Diarization

Identify different speakers:

```python
# Requires pyannote-audio
from pyannote.audio import Pipeline

def diarize_audio(audio_path: str) -> list:
    """Identify speakers in audio."""
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token="YOUR_HF_TOKEN"
    )

    diarization = pipeline(audio_path)

    speakers = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speakers.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })

    return speakers
```

## See Also

- [Multi-Modal Overview](index.md)
- [Vision Models](vision.md)
- [LocalAI Guide](../api-serving/localai.md)
