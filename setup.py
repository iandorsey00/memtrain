from setuptools import find_packages, setup


setup(
    name='memtrain',
    version='0.4.1',
    description='A program for better and less frustrating memorization',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'memtrain=memtrain.cli:main',
            'memtrain-gui=memtrain.gui:main',
        ],
    },
    python_requires='>=3.9',
)
