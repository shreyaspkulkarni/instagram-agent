import time
import base64
from backend.vision.scorer import _resize_for_scoring, _client, SCORE_PROMPT
from backend.vision.schemas import PhotoScore
from google.genai import types

IMAGE_PATH = "photos/IMG_7245_small.jpeg"

print("Reading photo...")
with open(IMAGE_PATH, "rb") as f:
    image_bytes = f.read()
print(f"Original size: {len(image_bytes) / 1024:.1f} KB")

print("Resizing...")
resized = _resize_for_scoring(image_bytes)
print(f"Resized size: {len(resized) / 1024:.1f} KB")

print("Calling Gemini (thinking disabled)...")
start = time.time()

response = _client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(data=resized, mime_type="image/jpeg"),
        SCORE_PROMPT,
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=PhotoScore,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
)

result = PhotoScore.model_validate_json(response.text)
elapsed = time.time() - start

print(f"\nDone in {elapsed:.1f}s")
print(f"Score:        {result.score}/10")
print(f"Post worthy:  {result.post_worthy}")
print(f"Format:       {result.recommended_format}")
print(f"Composition:  {result.composition_notes}")
print(f"Lighting:     {result.lighting_notes}")
print(f"\nEdit suggestions:")
for s in result.edit_suggestions:
    print(f"  - {s}")
print(f"\nEdit params (for Pillow):")
print(f"  rotation:   {result.edit_params.rotation}°")
print(f"  brightness: {result.edit_params.brightness:+.0f}")
print(f"  contrast:   {result.edit_params.contrast:+.0f}")
print(f"  saturation: {result.edit_params.saturation:+.0f}")
print(f"  sharpness:  {result.edit_params.sharpness:+.0f}")
print(f"  crop:       {result.edit_params.crop_ratio}")
