import ffmpeg
import os
from pprint import pp
import random
from parallel_tasks import ParallelRunner, Function, Task
# from parallel_tasks import enable_threaded_output, disable_threaded_output
from uuid import uuid4
import mimetypes
from .types import SizeVariant, VideoVariant, ImageItem, VideoObject


preset_variants = {
    SizeVariant.VIDEO240P: {
        'a_channels': 1,
        'a_preset': 8,
        'v_height': 240,
        'size_category': 0,
        'v_preset': 40
    },
    SizeVariant.VIDEO360P: {
        'a_channels': 1,
        'a_preset': 7,
        'v_height': 360,
        'size_category': 1,
        'v_preset': 39
    },
    SizeVariant.VIDEO480P: {
        'a_channels': 2,
        'a_preset': 6,
        'v_height': 480,
        'size_category': 2,
        'v_preset': 39
    },
    SizeVariant.VIDEO720P: {
        'a_channels': 2,
        'a_preset': 6,
        'v_height': 720,
        'size_category': 3,
        'v_preset': 38
    },
    SizeVariant.VIDEO1080P: {
        'a_channels': 2,
        'a_preset': 6,
        'v_height': 1080,
        'size_category': 4,
        'v_preset': 36
    }
}


class XXMPEG():
    def __init__(self, input: str):
        # read input and store it for stream selection
        if not os.path.exists(input):
            raise FileNotFoundError(f"Cannot find input file: {input}")
        self.input_path = input
        self.input = ffmpeg.input(input)
        self.probe = ffmpeg.probe(input)

        self.video_stream = None
        self.audio_stream = None
        self.original_size = 0
        self.original_duration = 0
        self.suppress_ffmpeg_output = True
        self.total_bitrate = 0
        self.__get_metdata()
        self.__selected_streams = ()
        # filename without extention to prepend to variant filenames
        self.__file_name = None
        if (basename := os.path.basename(self.input_path)):
            if (filename_split := os.path.splitext(basename)) and filename_split[1]:
                self.__file_name = filename_split[0]
        if not self.__file_name:
            self.__file_name = str(uuid4())

    def __get_metdata(self):
        if not (file_info := self.probe.get('format')):
            raise Exception("The file is invalid. Cannot get format information")
        self.original_size = file_info['size']
        self.original_duration = file_info['duration']
        self.total_bitrate = file_info['bit_rate']

    def __select_streams(self) -> tuple:
        if self.__selected_streams:
            return self.__selected_streams
        if not (streams := self.probe.get('streams')):
            raise Exception("The file doesn't contain any stream")
        v_stream_score = -1
        a_stream_score = -1
        video_stream = None
        audio_stream = None
        for (idx, stream) in enumerate(streams):
            if stream['codec_type'] == 'video':
                # score is based on height
                # TODO: score based on height closeness to the largest variant
                score = stream['height']
                if score > v_stream_score:
                    v_stream_score = score
                    video_stream = {
                        'stream': self.input[str(stream['index'])],
                        'metadata': stream
                    }
            elif stream['codec_type'] == 'audio':
                # score is based on channel count and language
                score = 0
                if stream['channels'] == 2:
                    score += 1000
                elif stream['channels'] > 2:
                    score += 500
                try:
                    lang = stream['tags']['language']
                    if lang == 'mal':
                        score += 1000
                    elif lang == 'eng':
                        score += 500
                except KeyError:
                    print(f"Language key not found on Stream #{idx}")
                if score > a_stream_score:
                    a_stream_score = score
                    audio_stream = {
                        'stream': self.input[str(stream['index'])],
                        'metadata': stream
                    }
        self.__selected_streams = (video_stream, audio_stream)
        return self.__selected_streams

    def __build_params(self, variants: SizeVariant, streams: list) -> list:
        # find which presets are requested and sort them
        selected_presets = []
        v_height = streams[0]['metadata']['height']
        v_width = streams[0]['metadata']['width']
        use_mono_audio = streams[1]['metadata']['channels'] == 1
        if use_mono_audio:
            print("Using mono audio since source only has mono")
        for (variant, preset) in preset_variants.items():
            if variant in variants:
                preset = preset.copy()
                use_mono_audio = use_mono_audio or preset['a_channels'] == 1
                if use_mono_audio:
                    preset['a_channels'] = 1
                preset['variant'] = variant
                preset['v_width'] = int((preset['v_height'] / v_height) * v_width)
                # width must be divisble by 2
                if preset['v_width'] % 2:
                    preset['v_width'] += 1
                selected_presets.append(preset)
        presets = sorted(selected_presets, key=lambda x: x['v_height'])
        presets.reverse()
        return presets

    def create_variants(self, variants: SizeVariant, output_path):
        input_streams = []
        if not variants:
            raise ValueError("Provide a valid variant to work with")
        if not os.path.exists(output_path):
            raise NotADirectoryError(f"The output path {output_path} isn't a directory")

        streams = self.__select_streams()
        # Add video stream to streams if available
        if not streams[0]:
            raise Exception("Input must have a video stream")
        else:
            input_streams.append(streams[0]['stream'])
        # Add audio stream to streams if available
        if streams[1]:
            input_streams.append(streams[1]['stream'])

        variants_params = self.__build_params(variants, streams)

        output_dir = f"{output_path}/{self.__file_name}"
        os.makedirs(output_dir, exist_ok=True)
        tasks = []
        generated_variants = []

        def _process_generated_variant(task):
            nonlocal generated_variants
            variant_path = task.return_data
            variant = self.variant_from_file(variant_path)
            if variant:
                generated_variants.append(variant)

        for variant_params in variants_params:
            variant_tag = f"{variant_params['size_category']}_{variant_params['v_height']}"
            variant_path = f"{output_dir}/{variant_tag}.mp4"
            function = Function(self.create_variant, [variant_params, input_streams, variant_path])
            callback = Function(_process_generated_variant)
            task = Task(target=function,
                        name=variant_tag,
                        callback=callback)
            tasks.append(task)
        runner = ParallelRunner(tasks)
        runner.run_all()
        return generated_variants

    def extract_frame(self, output_dir, seeker=0.2, thumbnail=False):
        """
        Seeker is a percent that determines how much time into the
        video should the frame be captured at
        """
        if seeker < 0 or seeker > 1:
            raise ValueError('seeker value must be less than 1 and greater than 0')
        streams = self.__select_streams()
        if not streams[0]:
            return None
        output_dir = f"{output_dir}/{self.__file_name}"
        os.makedirs(output_dir, exist_ok=True)
        video_stream = streams[0]
        stream_duration = float(video_stream['metadata']['duration'])
        capture_ts_1 = stream_duration * (seeker - 0.05)
        capture_ts_1 = min(0, capture_ts_1)
        capture_ts_2 = stream_duration * (seeker + 0.05)
        capture_ts_2 = max(1, capture_ts_2)
        # use a regeneratable seed so frame and thumb use  the smae timestamp
        random.seed(str(video_stream['stream']))
        capture_ts = random.uniform(capture_ts_1, capture_ts_2)
        args = {
            'vframes': 1,
            'ss': capture_ts
        }
        if thumbnail:
            h = w = 90
            # create thumbnail maintaining aspect ratio (adding black padding)
            filter_arg = f"scale={h}:{w}:force_original_aspect_ratio=decrease"
            filter_arg += f",pad={h}:{w}:-1:-1:color=black"
            args['filter:v'] = filter_arg
            path = f"{output_dir}/thumb.jpeg"
            size_category = 0
        else:
            path = f"{output_dir}/frame.jpeg"
            h = 480
            w = int((h / video_stream['metadata']['height']) * video_stream['metadata']['width'])
            if w % 2:
                w += 1
            size_category = 3
            args['filter:v'] = f"scale={w}:{h}"

        ffrun = ffmpeg.output(video_stream['stream'], path, **args)
        ffrun = ffrun.overwrite_output()
        print(' '.join(ffrun.compile()))
        ffrun.run(quiet=self.suppress_ffmpeg_output)
        if os.path.exists(path):
            image_item = ImageItem(path=path,
                                   mime_type=mimetypes.guess_type(path)[0],
                                   size=os.path.getsize(path),
                                   height=h,
                                   width=w,
                                   size_category=size_category
                                   )
            return image_item
        return None

    def variant_from_file(self, variant_path):
        if not os.path.exists(variant_path):
            raise FileNotFoundError(f"The variant not found at '{variant_path}'")
        probe_data = ffmpeg.probe(variant_path)
        video_stream = None
        audio_stream = None
        size_category = -1
        for stream in probe_data.get('streams'):
            if stream['codec_type'] == 'video':
                for (_, preset) in preset_variants.items():
                    if stream['height'] == preset['v_height']:
                        video_stream = stream
                        size_category = preset['size_category']
                        break
            # if stream['codec_type'] == 'audio':
            #     for (_, preset) in preset_variants.items():
            #         if stream['channels'] == preset['a_channels']:
            #             audio_stream = stream
            #             break
        if not video_stream:
            print(f"File '{variant_path}' didn't match any variants")
            return None
        try:
            variant = VideoVariant(
                            codec=video_stream['codec_name'],
                            height=video_stream['height'],
                            width=video_stream['width'],
                            duration=int(float(probe_data['format']['duration']) * 1000),
                            name=os.path.basename(variant_path),
                            ext=os.path.splitext(variant_path)[1].lstrip('.'),
                            size_category=size_category,
                            bitrate=video_stream['bit_rate'],
                            mime_type=mimetypes.guess_type(variant_path)[0])
        except Exception:
            return None
        return variant

    def possible_presets(self) -> list:
        streams = self.__select_streams()
        presets = {}
        if not streams[0]:
            raise Exception("The file doesn't contain a video stream")
        max_height = streams[0]['metadata']['height']
        for (variant, preset) in preset_variants.items():
            v_height = preset['v_height']
            if v_height <= max_height:
                presets[variant] = preset
            else:
                if (abs(v_height - max_height) / v_height) <= 0.1:
                    presets[variant] = preset
        return presets

    def create_variant(self, params, streams, output_path):
        args = {
            'vcodec': 'libx264',
            'pix_fmt': 'yuv420p',
            'acodec': 'libmp3lame',
            'format': 'mp4',
            'ac': params['a_channels'],
            'q:a': params['a_preset'],
            'crf': params['v_preset'],
            # filters for re-scaling and FPS
            'filter:v': f"scale={params['v_width']}:{params['v_height']},fps=24"
        }
        ffrun = ffmpeg.output(*streams, output_path, **args)
        ffrun = ffrun.overwrite_output()
        ffrun.run(quiet=self.suppress_ffmpeg_output)
        if os.path.exists(output_path):
            return output_path
        return None

    def generate_video_object(self, output_dir: str, variants: SizeVariant):
        print("-> Generating thumbnail")
        thumb = self.extract_frame(output_dir, thumbnail=True)
        print("-> Generating placeholder frame")
        frame = self.extract_frame(output_dir)
        print("-> Generating variants")
        vs = self.create_variants(variants, output_dir)
        # if 720p is available, set it as preferred quality
        # else, choose max
        max_size_category = max(vs, key=lambda x: x.size_category).size_category
        duration = 0
        for v in vs:
            duration = v.duration
            if v.size_category == 3:
                preferred_size_category = 3
                break
        else:
            preferred_size_category = max_size_category
        video_object = VideoObject(
            output_directory=f"{output_dir}/{self.__file_name}/",
            duration=duration,
            variants=vs,
            thumbnail=thumb,
            placeholder_frame=frame,
            maximum_size_category=max_size_category,
            preferred_size_category=preferred_size_category
        )
        return video_object
