"""Generate synthetic WebP avatars without external images or personal data."""

from io import BytesIO
from random import Random

from PIL import Image, ImageDraw


def avatar_bytes(seed: int) -> bytes:
    """Return a deterministic geometric avatar suitable for a fictitious profile."""
    random = Random(seed)
    background = tuple(random.randint(35, 210) for _ in range(3))
    accent = tuple(255 - component // 2 for component in background)
    image = Image.new("RGB", (256, 256), background)
    drawing = ImageDraw.Draw(image)

    drawing.ellipse((72, 38, 184, 150), fill=accent)
    drawing.rounded_rectangle((42, 142, 214, 266), radius=72, fill=accent)
    for _index in range(4):
        x = random.randint(10, 220)
        y = random.randint(10, 220)
        size = random.randint(8, 28)
        drawing.ellipse((x, y, x + size, y + size), outline="white", width=3)

    output = BytesIO()
    image.save(output, format="WEBP", quality=82, method=6, exif=b"")
    return output.getvalue()
