from logzero import setup_logger
from prettyprinter import cpprint
from dataclasses import dataclass
import random
from typing import Any
import ffmpeg
import os


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

    @property
    def frame_path(self):
        return f'{self.output_directory}/{self.name}_{self.height}p_frame.jpeg'


class XXMPEG:
    size_categories = [240, 360, 480, 720, 1080]

    def __init__(self, input_path, output_directory,
                 log_directory):
        self.input_path = input_path
        self.output_directory = output_directory.rstrip("/")
        self.name = os.path.basename(self.input_path)

        """
        All the resolutions that the video will be resized to.
        """
        self.active_sizes = []
        self.video = None
        self.video_probe = dict()
        self.video_variants = []

        if not os.path.isdir(self.output_directory):
            raise FileNotFoundError

        if not os.path.isfile(self.input_path):
            raise FileNotFoundError

        if not os.path.isdir(self.output_directory):
            raise FileNotFoundError

        self.logger = setup_logger(
            self.name,
            logfile=f'{log_directory}/{self.name}.log'
        )

        self.__ff_open()
        self.__generate_variants()

    def __ff_open(self):
        probe = ffmpeg.probe(self.input_path)
        """
        Get the video stream
        """
        video_stream = probe['streams'][0]

        """
        Check if an audio stream is available
        """
        has_audio = False
        for stream in probe['streams']:
            if stream['codec_type'] == "audio":
                has_audio = True

        orig_width = video_stream['width']
        orig_height = video_stream['height']
        codec = video_stream['codec_name']
        duration = float(video_stream['duration'])
        name, ext = os.path.splitext(os.path.basename(self.input_path))
        
        extract_time = random.randrange(1, int(duration))
        print(extract_time)
        print(duration)
        self.video = InputVideo(
            path=self.input_path,
            height=orig_height,
            width=orig_width,
            codec=codec,
            has_audio=has_audio,
            duration=duration,
            ffmpeg=ffmpeg.input(self.input_path),
            name=name,
            ext=ext,
            extract_time=extract_time
        )

    def __create_variant(self, height, width, size_category):
        return VideoVariant(
            output_directory=self.output_directory,
            codec='mpeg',
            height=height,
            width=width,
            duration=self.video.duration,
            name=self.video.name,
            ext='mp4',
            ffmpeg=self.video.ffmpeg,
            size_category=size_category,
        )

    def __generate_variants(self):
        closest_size_category = None
        diff_comp = -1

        for index, size_category in enumerate(self.size_categories):
            diff = abs(size_category - self.video.height)
            if diff_comp < 0:
                diff_comp = diff
                continue

            if diff < diff_comp:
                diff_comp = diff
                closest_size_category = index

        self.generated_sizes = self.size_categories[0:closest_size_category]
        self.generated_sizes.append(self.video.height)

        for size_category, height in enumerate(self.generated_sizes):
            new_height, new_width = self.__downsample_size(height)
            variant = self.__create_variant(new_height, new_width,
                                            size_category)
            self.video_variants.append(variant)

    def __downsample_size(self, new_height):
        factor = self.video.width / self.video.height
        new_width = int(new_height * factor)
        if not new_width % 2 == 0:
            new_width = new_width + 1
        return (new_height, new_width)

    def output(self):
        self.video_variants = [self.video_variants[0]]
        for variant in self.video_variants:
            streams = []
            video = variant.ffmpeg.video
            video = video.filter('scale', variant.width, variant.height)
            video = video.filter('fps', 24)
            streams.append(video)

            if self.video.has_audio:
                audio = self.video.ffmpeg.audio
                streams.append(audio)

            args = {
                'vcodec': 'libx264',
                'acodec': 'libmp3lame',
                'video_bitrate': '2.5M',
                'format': 'mp4'
            }
            y = out = (
                ffmpeg.output(*streams, variant.path, **args)
                .overwrite_output()
            )
            f = out.run(quiet=True)
            frame_out = (
                ffmpeg
                .output(video, variant.frame_path, vframes=1)
                .overwrite_output()
            )
            frame_out.run(quiet=True)
            cpprint(y)
            cpprint(f)

        return self.video_variants
