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
