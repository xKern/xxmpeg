from dataclasses import dataclass
from typing import Any, List, Optional
import os


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
    mime_type: str = 'image/jpeg'

    @property
    def size(self):
        return os.stat(self.path).st_size

    @property
    def aspect_ratio(self):
        return (self.width / self.height)

    @property
    def filename(self):
        return f'{self.name}_{self.height}p.{self.ext}'

    @property
    def path(self):
        return f'{self.output_directory}/{self.filename}'


@dataclass
class ImageVariant:
    output_directory: str
    name: str
    height: int
    width: int
    form: str = 'frame'
    ext: str = 'jpeg'
    mime_type: str = 'image/jpeg'

    @property
    def size(self):
        return os.stat(self.path).st_size

    @property
    def filename(self):
        return f'{self.name}_{self.form}.{self.ext}'

    @property
    def path(self):
        return f'{self.output_directory}/{self.filename}'

    @property
    def aspect_ratio(self):
        return (self.width / self.height)


@dataclass
class VideoObject:
    name: str
    output_directory: str
    duration: float
    variants: Optional[List[VideoVariant]]
    thumbnail: ImageVariant
    placeholder_frame: ImageVariant
    maximum_size_category: int = 0
    preferred_size_category: int = 0
