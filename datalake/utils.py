import base64
import io
import requests
from PIL import Image
from typing import Optional


def to_base64(im: Image.Image) -> str:
    file_object = io.BytesIO()
    im.save(file_object, 'JPEG')
    file_object.seek(0)
    b64 = base64.b64encode(file_object.read()).decode('utf-8')
    src = f"data:image/jpeg;charset=utf-8;base64, {b64}"
    return src


def from_url(image_url: str) -> Optional[Image.Image]:
    image_url = image_url.split('?')[0]
    r = requests.get(image_url, stream=True)
    if r.status_code == 200:
        return Image.open(io.BytesIO(r.content)).convert("RGB")
