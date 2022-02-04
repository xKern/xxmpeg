from xxmpeg import XXMPEG

a = XXMPEG(input_path='/home/neo/work/xkern/xmptest/input/testy.mp4',
           output_directory='/home/neo/work/xkern/xmptest/output/',
           log_directory='/home/neo/work/xkern/xmptest/logs/')
video_object = a.output()
print(video_object)
