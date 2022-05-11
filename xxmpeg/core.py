from logzero import setup_logger
from .objects import (
    VideoObject,
    VideoVariant,
    ImageVariant,
    InputVideo
)
from parallel_tasks import (
    ParallelRunner,
    Function,
    Task
)
import random
import ffmpeg
import os


class XXMPEG:
    size_categories = [240, 360, 480, 720, 1080]

    def __init__(self, input_path, output_directory,
                 log_directory):
        self.input_path = input_path
        self.output_directory = output_directory.rstrip("/")
        self.name = os.path.basename(self.input_path)
        self.probe = None

        """
        All the resolutions that the video will be resized to.
        """
        self.active_sizes = []
        self.video = None
        self.video_probe = dict()
        self.video_variants = []
        self.video_object = None

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

    def __factory_input_video(self):
        """
        Factory method to create InputVideo
        """
        video_stream = self.probe['streams'][0]
        orig_width = video_stream['width']
        orig_height = video_stream['height']
        codec = video_stream['codec_name']

        try:
            duration = float(video_stream['duration'])
        except KeyError:
            """
            MKV Files duration is not available in the stream probe
            """
            duration = float(self.probe['format']['duration'])

        name, ext = os.path.splitext(os.path.basename(self.input_path))
        extract_time = random.randrange(1, int(duration))

        has_audio = False
        for stream in self.probe['streams']:
            if stream['codec_type'] == "audio":
                has_audio = True

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

    def __factory_video_object(self):
        frame = ImageVariant(
            output_directory=self.output_directory,
            name=self.video.name,
            height=self.video.height,
            width=self.video.width,
            form='frame'
        )
        thumb = ImageVariant(
            output_directory=self.output_directory,
            name=self.video.name,
            height=250,
            width=250,
            form='thumb'
        )
        self.video_object = VideoObject(
            output_directory=self.output_directory,
            name=self.video.name,
            duration=self.video.duration,
            thumbnail=thumb,
            placeholder_frame=frame,
            variants=[]
        )

    def __ff_open(self):
        self.probe = ffmpeg.probe(self.input_path)
        self.__factory_input_video()
        self.__factory_video_object()

    def __create_variant(self, height, width, size_category):
        return VideoVariant(
            output_directory=self.output_directory,
            codec='libx264',
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

        preferred_size_category = len(self.generated_sizes) - 1

        """
        These two properties were ommited in the factory method
        """
        self.video_object.maximum_size_category = preferred_size_category
        self.video_object.preferred_size_category = preferred_size_category

        for size_category, height in enumerate(self.generated_sizes):
            new_height, new_width = self.__downsample_size(height)
            variant = self.__create_variant(new_height, new_width,
                                            size_category)
            self.video_object.variants.append(variant)

    def __downsample_size(self, new_height):
        factor = self.video.width / self.video.height
        new_width = int(new_height * factor)
        if not new_width % 2 == 0:
            new_width = new_width + 1
        return (new_height, new_width)

    def __get_variant_metadata(self, variant):
        probe = ffmpeg.probe(variant.path)
        video_stream = probe['streams'][0]
        return {
            'bitrate': int(video_stream.get('bit_rate')),
        }

    def actual_work(self, variant):
        streams = []
        video = variant.ffmpeg.video
        video = video.filter('scale', variant.width, variant.height)
        video = video.filter('fps', 24)
        streams.append(video)

        if self.video.has_audio:
            audio = self.video.ffmpeg.audio
            streams.append(audio)

        target_bitrate = min(variant.height, variant.width) / 1.8
        args = {
            'vcodec': 'libx264',
            'acodec': 'libmp3lame',
            'video_bitrate': f'{target_bitrate}k',
            'format': 'mp4'
        }
        out = (
            ffmpeg.output(*streams, variant.path, **args)
            .overwrite_output()
        )
        out.run(quiet=False)
        """
        Update VideoVariant.bitrate, VideoVariant.size,
            VideoVariant.aspect_ratio
        """
        metadata = self.__get_variant_metadata(variant)
        variant.bitrate = metadata['bitrate']

    def output(self):
        variants = self.video_object.variants
        tasks = []
        for variant in variants:
            # self.actual_work(variant)
            func = Function(target=self.actual_work, arguments={'variant':
                                                                variant})
            task = Task(name='proc_video', target=func)
            tasks.append(task)

        runner = ParallelRunner(tasks=tasks)
        runner.run_all()

        video = self.video.ffmpeg
        """
        Create placeholder frame
        """
        frame_out = (
            ffmpeg
            .output(video, self.video_object.placeholder_frame.path, vframes=1,
                    ss=self.video.extract_time)
            .overwrite_output()
        )
        frame_out.run(quiet=True)

        """
        Create thumbnail
        """
        video = self.video.ffmpeg.video
        video = video.filter('scale', 250, 250)
        thumb_out = (
            ffmpeg
            .output(video, self.video_object.thumbnail.path, vframes=1,
                    ss=self.video.extract_time)
            .overwrite_output()
        )
        thumb_out.run(quiet=True)

        return self.video_object
