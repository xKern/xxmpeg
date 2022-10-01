from distutils.core import setup
setup(
      name='xxmpeg',
      packages=['xxmpeg'],
      version='2.0',
      license='MIT',
      description=('Trancoder based on ffmpeg to create video variants,'
                   'placeholder image and thumbnail from a video container'),
      author='ARX8x, Haider Ali',
      author_email='root@xken.net',
      url='https://github.com/xKern/xxmpeg',
      keywords=['xKern', 'xxmpeg', 'trascoder', 'mediaobject', 'ffmpeg', 'ffprobe'],
      install_requires=[
        'ffmpeg-python==0.1.18',
        'opencv-python',
        'logzero',
        'parallel_tasks @ git+https://github.com/arx8x/py-parallel-tasks.git'
      ],
      classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.9',
        ],
)
