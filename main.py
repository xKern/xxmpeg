from xxmpeg import XXMPEG

try:
    a = XXMPEG(input_path='/home/neo/work/xkern/xmptest/input/aqua.wmv',
               output_directory='/home/neo/work/xkern/xmptest/output/',
               log_directory='/home/neo/work/xkern/xmptest/logsz/')
    variants = a.output()
    print(len(variants))
except Exception as e:
    print(str(e))
