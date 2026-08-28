"""Security tests for untrusted profile-image decoding."""

from io import BytesIO

import pytest
from PIL import Image

from app.photos.image_processing import InvalidImageError, process_image


def image_bytes(image_format: str, size: tuple[int, int] = (32, 24)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, "#ff5149").save(output, format=image_format)
    return output.getvalue()


@pytest.mark.parametrize("image_format", ["JPEG", "PNG", "WEBP"])
def test_allowed_images_are_reencoded_as_metadata_free_webp(image_format: str) -> None:
    result = process_image(image_bytes(image_format))
    assert result.mime_type == "image/webp"
    assert (result.width, result.height) == (32, 24)
    with Image.open(BytesIO(result.content)) as decoded:
        assert decoded.format == "WEBP"
        assert not decoded.getexif()


def test_invalid_and_animated_files_are_rejected() -> None:
    with pytest.raises(InvalidImageError):
        process_image(b"<svg><script>alert(1)</script></svg>")
    animated = BytesIO()
    frames = [Image.new("RGB", (4, 4), color) for color in ("red", "blue")]
    frames[0].save(animated, format="GIF", save_all=True, append_images=frames[1:])
    with pytest.raises(InvalidImageError):
        process_image(animated.getvalue())


def test_oversized_dimensions_and_files_are_rejected() -> None:
    with pytest.raises(InvalidImageError):
        process_image(image_bytes("PNG", (4097, 1)))
    with pytest.raises(InvalidImageError):
        process_image(b"x" * (5 * 1024 * 1024 + 1))
