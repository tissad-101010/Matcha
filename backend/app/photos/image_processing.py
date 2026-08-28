"""Decode and neutralize untrusted profile images with Pillow."""

from dataclasses import dataclass
from io import BytesIO
from warnings import catch_warnings, simplefilter

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_SIDE = 4096
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class InvalidImageError(Exception):
    """Raised when uploaded bytes do not satisfy the mandatory image policy."""


@dataclass(frozen=True)
class ProcessedImage:
    content: bytes
    width: int
    height: int
    mime_type: str = "image/webp"


def process_image(content: bytes) -> ProcessedImage:
    """Validate real bytes, remove metadata and return a fresh WebP encoding."""
    if not content or len(content) > MAX_IMAGE_BYTES:
        raise InvalidImageError("L’image doit peser au maximum 5 Mio.")
    try:
        with catch_warnings():
            simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in ALLOWED_FORMATS:
                    raise InvalidImageError("Seuls JPEG, PNG et WebP sont acceptés.")
                if getattr(source, "is_animated", False) or getattr(source, "n_frames", 1) != 1:
                    raise InvalidImageError("Les images animées sont interdites.")
                if not _valid_dimensions(*source.size):
                    raise InvalidImageError("L’image ne doit pas dépasser 4096 × 4096 pixels.")
                source.load()
                transposed = ImageOps.exif_transpose(source)
                clean = transposed.convert("RGBA" if "A" in transposed.getbands() else "RGB")
                width, height = clean.size
                output = BytesIO()
                clean.save(output, format="WEBP", quality=88, method=6, exif=b"")
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        raise InvalidImageError("Le fichier fourni n’est pas une image valide.") from error
    return ProcessedImage(output.getvalue(), width, height)


def _valid_dimensions(width: int, height: int) -> bool:
    return 1 <= width <= MAX_IMAGE_SIDE and 1 <= height <= MAX_IMAGE_SIDE
