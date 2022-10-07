from dataclasses import dataclass
from typing import List, Optional
import os
from enum import IntFlag, auto


class SizeVariant(IntFlag):
    VIDEO240P = auto()
    VIDEO360P = auto()
    VIDEO480P = auto()
    VIDEO720P = auto()
    VIDEO1080P = auto()
    SD = VIDEO240P | VIDEO360P | VIDEO480P
    HD = VIDEO720P | VIDEO1080P
    ALL = SD | HD


@dataclass
class VideoVariant:
    path: str
    codec: str
    height: float
    width: float
    duration: float
    name: str
    ext: str
    size_category: int
    bitrate: int
    mime_type: str

    @property
    def size(self):
        return os.stat(self.path).st_size

    @property
    def aspect_ratio(self):
        return (self.width / self.height)

    @property
    def filename(self):
        return self.name


@dataclass
class ImageItem:
    path: str
    mime_type: str
    size: int
    height: int
    width: int
    size_category: int

    @property
    def aspect_ratio(self):
        return (self.width / self.height)

    @property
    def filename(self):
        return os.path.basename(self.path)


@dataclass
class VideoObject:
    output_directory: str
    duration: float
    variants: Optional[List[VideoVariant]]
    thumbnail: ImageItem
    placeholder_frame: ImageItem
    maximum_size_category: int = 0
    preferred_size_category: int = 0

    @property
    def name(self):
        return os.path.basename(self.output_directory)
