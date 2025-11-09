import logging
import math
import os
import shutil
import subprocess
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, ImageOps


@dataclass
class ImageCompressionConfig:
    max_edge: int = 1440
    quality: int = 88
    min_quality: int = 75
    target_max_kb: int = 600
    target_min_kb: int = 200
    allow_webp: bool = True


@dataclass
class VideoCompressionConfig:
    target_width: int = 720
    max_height: int = 1280
    max_bitrate: str = "1200k"
    min_bitrate: str = "800k"
    audio_bitrate: str = "96k"
    frame_rate: int = 30
    max_duration: Optional[int] = None


IMAGE_CONFIG = ImageCompressionConfig(
    **getattr(settings, "MEDIA_IMAGE_COMPRESSION", {})
)
VIDEO_CONFIG = VideoCompressionConfig(
    **getattr(settings, "MEDIA_VIDEO_COMPRESSION", {})
)


logger = logging.getLogger(__name__)


def _resolve_ffmpeg_binary() -> Tuple[str, str]:
    ffmpeg_bin = getattr(settings, "FFMPEG_BIN", shutil.which("ffmpeg"))
    ffprobe_bin = getattr(settings, "FFPROBE_BIN", shutil.which("ffprobe"))
    if not ffmpeg_bin or not ffprobe_bin:
        raise RuntimeError("ffmpeg/ffprobe binaries are required for video compression")
    return ffmpeg_bin, ffprobe_bin


def _determine_image_format(image: Image.Image, config: ImageCompressionConfig) -> Tuple[str, str]:
    """Return (format, extension)."""
    has_alpha = image.mode in {"LA", "RGBA", "P"} and (
        image.mode != "P" or image.info.get("transparency") is not None
    )
    if has_alpha and config.allow_webp:
        return "WEBP", ".webp"
    return "JPEG", ".jpg"


def compress_image(
    uploaded_file: UploadedFile,
    config: Optional[ImageCompressionConfig] = None,
) -> Tuple[ContentFile, str]:
    """Compress an uploaded image and return (file, filename)."""
    uploaded_file.seek(0)
    cfg = config or IMAGE_CONFIG

    with Image.open(uploaded_file) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "RGBA", "P", "LA"):
            img = img.convert("RGB")

        max_edge = cfg.max_edge
        long_edge = max(img.width, img.height)
        if long_edge > max_edge:
            scale = max_edge / long_edge
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)

        target_format, ext = _determine_image_format(img, cfg)
        quality = cfg.quality
        min_quality = cfg.min_quality

        buffer = BytesIO()
        size_kb = None
        while True:
            buffer.seek(0)
            buffer.truncate()
            save_kwargs = {"format": target_format, "quality": quality}
            if target_format == "JPEG":
                save_kwargs.update({"optimize": True, "progressive": True})
                if img.mode in ("RGBA", "LA"):
                    img_to_save = img.convert("RGB")
                else:
                    img_to_save = img
            else:
                img_to_save = img
                save_kwargs.setdefault("method", 6)

            img_to_save.save(buffer, **save_kwargs)
            size_kb = math.ceil(buffer.tell() / 1024)

            if size_kb <= cfg.target_max_kb or quality <= min_quality:
                break
            quality = max(min_quality, quality - 5)

        filename = f"{Path(uploaded_file.name).stem}{ext}"
        compressed_content = ContentFile(buffer.getvalue())
        compressed_content.name = filename
        compressed_content.size = buffer.tell()
        return compressed_content, filename


def _write_temp_file(uploaded_file: UploadedFile, suffix: Optional[str] = None) -> str:
    import tempfile

    uploaded_file.seek(0)
    suffix = suffix or Path(uploaded_file.name).suffix or ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        for chunk in uploaded_file.chunks():
            temp.write(chunk)
        temp_path = temp.name
    return temp_path


def _probe_video_duration(ffprobe_bin: str, file_path: str) -> Optional[float]:
    try:
        result = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.CalledProcessError):
        return None


def _wrap_original_upload(uploaded_file: UploadedFile) -> Tuple[ContentFile, str]:
    """Return the original upload as ContentFile when compression is unavailable."""
    uploaded_file.seek(0)
    if hasattr(uploaded_file, "chunks"):
        buffer = BytesIO()
        for chunk in uploaded_file.chunks():
            buffer.write(chunk)
        data = buffer.getvalue()
    else:
        data = uploaded_file.read()
    filename = Path(uploaded_file.name or "upload").name
    original_content = ContentFile(data)
    original_content.name = filename
    return original_content, filename


def compress_video(
    uploaded_file: UploadedFile,
    config: Optional[VideoCompressionConfig] = None,
) -> Tuple[ContentFile, str]:
    cfg = config or VIDEO_CONFIG
    try:
        ffmpeg_bin, ffprobe_bin = _resolve_ffmpeg_binary()
    except RuntimeError as exc:
        logger.warning("FFmpeg binaries not found, storing original video: %s", exc)
        return _wrap_original_upload(uploaded_file)
    input_path = _write_temp_file(uploaded_file)
    output_suffix = ".mp4"
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=output_suffix) as temp_output:
        output_path = temp_output.name

    try:
        duration = _probe_video_duration(ffprobe_bin, input_path)
        if cfg.max_duration and duration and duration > cfg.max_duration:
            raise ValueError("Video duration exceeds maximum allowed length")

        scale_filter = f"scale='min({cfg.target_width},iw)':-2"
        vf_filters = [scale_filter]
        command = [
            ffmpeg_bin,
            "-y",
            "-i",
            input_path,
            "-vf",
            ",".join(vf_filters),
            "-r",
            str(cfg.frame_rate),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            cfg.max_bitrate,
            "-maxrate",
            cfg.max_bitrate,
            "-bufsize",
            "2400k",
            "-c:a",
            "aac",
            "-b:a",
            cfg.audio_bitrate,
            "-movflags",
            "+faststart",
            output_path,
        ]
        result = subprocess.run(command, capture_output=True)
        if result.returncode != 0 or not os.path.exists(output_path):
            stderr = result.stderr.decode("utf-8", "ignore")
            logger.warning("FFmpeg compression failed (%s). Falling back to original video.", stderr.strip())
            return _wrap_original_upload(uploaded_file)

        with open(output_path, "rb") as output_file:
            data = output_file.read()
        filename = f"{Path(uploaded_file.name).stem}{output_suffix}"
        compressed_content = ContentFile(data)
        compressed_content.name = filename
        return compressed_content, filename
    finally:
        try:
            os.remove(input_path)
        except OSError:
            pass
        try:
            os.remove(output_path)
        except OSError:
            pass
