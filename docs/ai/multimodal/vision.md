# Vision Models

Local vision models enable image understanding, OCR, and visual question answering.

## Available Models

### Ollama Vision Models

```bash
# Small and fast
ollama pull moondream        # 1.6B - Quick descriptions
ollama pull minicpm-v        # 3B - Efficient vision

# Standard quality
ollama pull llava            # 7B - Good balance
ollama pull llava-llama3     # 8B - Latest Llama architecture

# High quality
ollama pull llava:13b        # 13B - Better accuracy
ollama pull llava:34b        # 34B - Best quality
```

### Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| moondream | 1.6B | Very fast | Basic | Quick checks |
| minicpm-v | 3B | Fast | Good | Mobile/edge |
| llava | 7B | Medium | Good | General use |
| llava-llama3 | 8B | Medium | Better | Latest features |
| llava:13b | 13B | Slow | Better | Detailed analysis |
| llava:34b | 34B | Very slow | Best | Maximum accuracy |

## Basic Usage

### Python with Ollama

```python
import ollama
import base64
from pathlib import Path

def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def analyze_image(image_path: str, prompt: str = "Describe this image") -> str:
    """Analyze an image with a vision model."""
    image_data = encode_image(image_path)

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_data]
        }]
    )

    return response["message"]["content"]

# Usage
description = analyze_image("photo.jpg")
print(description)
```

### OpenAI-Compatible API

```python
from openai import OpenAI
import base64

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

def analyze_image_openai(image_path: str, prompt: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = client.chat.completions.create(
        model="llava",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        }],
        max_tokens=500
    )

    return response.choices[0].message.content
```

### URL Images

```python
response = client.chat.completions.create(
    model="llava",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {"url": "https://example.com/image.jpg"}
            }
        ]
    }]
)
```

## Common Tasks

### Image Description

```python
def describe_image(image_path: str, detail_level: str = "detailed") -> str:
    prompts = {
        "brief": "Describe this image in one sentence.",
        "detailed": "Describe this image in detail, including objects, colors, and composition.",
        "technical": "Provide a technical analysis of this image including lighting, composition, and quality."
    }

    return analyze_image(image_path, prompts[detail_level])
```

### OCR (Text Extraction)

```python
def extract_text(image_path: str) -> str:
    """Extract text from an image."""
    prompt = """Extract all text visible in this image.
    Return only the text, preserving the layout as much as possible.
    If no text is visible, return 'No text found'."""

    return analyze_image(image_path, prompt)

def extract_structured_text(image_path: str) -> dict:
    """Extract text with structure."""
    prompt = """Extract all text from this image and return it as JSON:
    {
        "title": "any title or heading",
        "body": "main text content",
        "labels": ["any labels or tags"],
        "numbers": ["any numbers or values"]
    }
    Return only valid JSON."""

    response = analyze_image(image_path, prompt)

    import json
    try:
        return json.loads(response)
    except:
        return {"raw_text": response}
```

### Visual Question Answering

```python
def ask_about_image(image_path: str, question: str) -> str:
    """Ask a specific question about an image."""
    return analyze_image(image_path, question)

# Examples
count = ask_about_image("crowd.jpg", "How many people are in this image?")
color = ask_about_image("car.jpg", "What color is the car?")
location = ask_about_image("landmark.jpg", "Where was this photo taken?")
```

### Image Comparison

```python
def compare_images(image1_path: str, image2_path: str) -> str:
    """Compare two images."""
    img1_data = encode_image(image1_path)
    img2_data = encode_image(image2_path)

    response = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": "Compare these two images. What are the similarities and differences?",
            "images": [img1_data, img2_data]
        }]
    )

    return response["message"]["content"]
```

### Chart/Graph Analysis

```python
def analyze_chart(image_path: str) -> str:
    """Analyze a chart or graph."""
    prompt = """Analyze this chart/graph:
    1. What type of chart is this?
    2. What data is being presented?
    3. What are the key trends or insights?
    4. What are the approximate values shown?"""

    return analyze_image(image_path, prompt)
```

### Code Screenshot Analysis

```python
def analyze_code_screenshot(image_path: str) -> str:
    """Extract and analyze code from a screenshot."""
    prompt = """This is a screenshot of code.
    1. Extract the code exactly as shown
    2. Identify the programming language
    3. Explain what the code does
    4. Note any potential issues or improvements"""

    return analyze_image(image_path, prompt)
```

## Batch Processing

```python
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def process_images(image_dir: str, prompt: str) -> dict:
    """Process multiple images."""
    results = {}
    image_paths = list(Path(image_dir).glob("*.jpg")) + list(Path(image_dir).glob("*.png"))

    def process_single(path):
        return str(path), analyze_image(str(path), prompt)

    with ThreadPoolExecutor(max_workers=4) as executor:
        for path, result in executor.map(lambda p: process_single(p), image_paths):
            results[path] = result

    return results

# Usage
descriptions = process_images("./photos", "Describe this image briefly")
```

## Integration with RAG

```python
def vision_enhanced_rag(image_path: str, query: str, vectorstore) -> str:
    """Combine vision analysis with RAG."""

    # Get image description
    image_context = analyze_image(image_path, "Describe this image in detail")

    # Retrieve relevant documents
    docs = vectorstore.similarity_search(query, k=3)
    doc_context = "\n".join([doc.page_content for doc in docs])

    # Combined query
    combined_prompt = f"""Image description: {image_context}

    Related documents:
    {doc_context}

    Based on the image and documents above, answer: {query}"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": combined_prompt}]
    )

    return response["message"]["content"]
```

## Streaming Responses

```python
def analyze_image_stream(image_path: str, prompt: str):
    """Stream the analysis response."""
    image_data = encode_image(image_path)

    stream = ollama.chat(
        model="llava",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_data]
        }],
        stream=True
    )

    for chunk in stream:
        print(chunk["message"]["content"], end="", flush=True)
    print()
```

## Error Handling

```python
def safe_analyze_image(image_path: str, prompt: str) -> dict:
    """Analyze image with error handling."""
    try:
        # Validate file exists
        if not Path(image_path).exists():
            return {"error": "File not found", "success": False}

        # Check file size (limit to 20MB)
        if Path(image_path).stat().st_size > 20 * 1024 * 1024:
            return {"error": "File too large", "success": False}

        result = analyze_image(image_path, prompt)
        return {"result": result, "success": True}

    except Exception as e:
        return {"error": str(e), "success": False}
```

## Performance Tips

### Model Selection

```python
def select_model(task: str, speed_priority: bool = False) -> str:
    """Select appropriate model for task."""
    if speed_priority:
        return "moondream"

    task_models = {
        "quick_check": "moondream",
        "general": "llava",
        "ocr": "llava-llama3",
        "detailed": "llava:13b",
        "analysis": "llava:34b"
    }

    return task_models.get(task, "llava")
```

### Image Preprocessing

```python
from PIL import Image

def preprocess_image(image_path: str, max_size: int = 1024) -> str:
    """Resize large images before processing."""
    img = Image.open(image_path)

    # Resize if too large
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.LANCZOS)

    # Save to temp file
    import tempfile
    temp_path = tempfile.mktemp(suffix=".jpg")
    img.save(temp_path, "JPEG", quality=85)

    return temp_path
```

## See Also

- [Multi-Modal Overview](index.md)
- [Audio Processing](audio.md)
- [Ollama Guide](../inference-engines/ollama/index.md)
