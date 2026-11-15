import math
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 25_000_000
MAX_DIMENSION = 10_000
MAX_DECODE_PIXELS = 50_000_000
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageProcessingError(Exception):
    """Raised when an image cannot be prepared for OCR."""


def prepare_image(
    data: bytes,
    content_type: str | None = None,
    filename: str | None = None,
) -> tuple[bytes, str, str]:
    """Return bytes, MIME type and filename that fit the extractor limits."""
    if not data:
        raise ImageProcessingError("Image is empty.")

    try:
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
            if width * height > MAX_DECODE_PIXELS:
                raise ImageProcessingError("Image has too many pixels to process.")

            needs_processing = (
                len(data) > MAX_BYTES
                or width > MAX_DIMENSION
                or height > MAX_DIMENSION
                or width * height > MAX_PIXELS
                or image.format not in ALLOWED_FORMATS
                or image.getexif().get(274, 1) != 1
            )

            if not needs_processing:
                return (
                    data,
                    image.get_format_mimetype()
                    or content_type
                    or "application/octet-stream",
                    filename or "image",
                )

            image = ImageOps.exif_transpose(image)
            width, height = image.size
            scale = min(
                1.0,
                MAX_DIMENSION / max(width, height),
                math.sqrt(MAX_PIXELS / (width * height)),
            )
            if scale < 1.0:
                image = image.resize(
                    (max(1, int(width * scale)), max(1, int(height * scale))),
                    Image.Resampling.LANCZOS,
                )

            return _encode_jpeg(image), "image/jpeg", "image.jpg"
    except ImageProcessingError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise ImageProcessingError("Unsupported or invalid image.") from exc


def _encode_jpeg(image: Image.Image) -> bytes:
    for _ in range(3):
        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")

        for quality in (90, 80, 70):
            buffer = BytesIO()
            image.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            if buffer.tell() <= MAX_BYTES:
                return buffer.getvalue()

        scale = math.sqrt(MAX_BYTES / buffer.tell()) * 0.95
        if scale >= 1.0:
            break
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )

    raise ImageProcessingError("Image is still larger than 15 MiB after compression.")
