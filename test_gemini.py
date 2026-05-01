import base64
import instructor
from openai import OpenAI
from backend.config import settings
from backend.vision.schemas import PhotoScore

print("API key loaded:", bool(settings.google_api_key))

client = instructor.from_openai(
    OpenAI(
        api_key=settings.google_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
)

# Test with a tiny solid-color image (no file needed)
import struct, zlib

def make_tiny_png():
    def chunk(name, data):
        c = name + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00'))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

image_b64 = base64.standard_b64encode(make_tiny_png()).decode()

print("Calling Gemini...")
result = client.chat.completions.create(
    model="gemini-2.5-flash",
    response_model=PhotoScore,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            {"type": "text", "text": "Score this image for Instagram. It is a test image."},
        ],
    }],
)
print("Success! Score:", result.score)
print("Post worthy:", result.post_worthy)
