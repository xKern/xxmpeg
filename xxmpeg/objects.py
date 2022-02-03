from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class InputVideo:
    path: str
    codec: str
    has_audio: bool
    height: float
    width: float
    duration: int
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
    duration: int
    name: str
    ext: str
    size_category: int
    ffmpeg: Any

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
    maximum_size_category: int
    preferred_size_category: int
    duration: int
    variants: Optional[List[VideoVariant]]

    @property
    def thumbnail(self):
        return f'{self.output_directory}/{self.name}_thumb.jpeg'

    @property
    def frame_path(self):
        return f'{self.output_directory}/{self.name}_{self.height}p_frame.jpeg'
