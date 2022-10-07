from xxmpeg import XXMPEG
video = XXMPEG('/path/to/input.mp4')
presets = video.possible_presets()
video_object = video.generate_video_object('./output_dir/', presets)
