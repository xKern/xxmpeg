from distutils.core import setup
setup(
      name='xxmpeg',         # How you named your package folder (MyLib)
      packages=['xxmpeg'],   # Chose the same as "name"
      version='0.0.2',
      license='MIT',
      description=('Simple wrapper atop ffmpeg to resize videos '
                   'into multiple variants'),
      author='Haider Ali',                   # Type in your name
      author_email='me@haiderali.dev',      # Type in your E-Mail
      url='https://github.com/xKern/xxmpeg',
      keywords=['XKERN', 'XXMPEG', 'PYTHON', 'FFMPEG', 'OPENCV'],
      install_requires=['ffmpeg-python==0.1.18', 'opencv-python', 'logzero'],
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Build Tools',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.10',
        ],
)
