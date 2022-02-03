from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class InputVideo:
    path: str
    codec: str
    has_audio: bool
    height: float
    width: float
    duration: float
    name: str
    ext: str
    ffmpeg: Any
    extract_time: int


@dataclass
class VideoVariant:
    output_directory: str
    codec: str
    height: float
    width: float
    duration: float
    name: str
    ext: str
    size_category: int
    ffmpeg: Any
    bitrate: int = 0
    size: int = 0
    aspect_ratio: float = 0

    @property
    def mime_type(self):
        return 'video/mpeg4'

    @property
    def filename(self):
        return f'{self.name}_{self.height}p.{self.ext}'

    @property
    def path(self):
        return f'{self.output_directory}/{self.filename}'


@dataclass
class VideoObject:
    name: str
    output_directory: str
    duration: float
    variants: Optional[List[VideoVariant]]
    maximum_size_category: int = 0
    preferred_size_category: int = 0

    @property
    def thumbnail(self):
        return f'{self.output_directory}/{self.name}_thumb.jpeg'

    @property
    def placeholder_frame(self):
        return f'{self.output_directory}/{self.name}_frame.jpeg'
