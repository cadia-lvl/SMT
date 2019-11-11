from setuptools import setup
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='corpus',
    version='1.1.1',
    author='Haukur Páll Jónsson',
    author_email='haukurpalljonsson@gmail.com',
    url='https://github.com/cadia-lvl/SMT/tree/master/corpus',
    description='A library to process corpora.',
    license='MIT',
    python_requires='>=3.7.*',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['corpus', 'cli'],
    include_package_data=True,
    install_requires=[
        'Click',
        'nltk',
        'sacremoses',
        'tokenizer',
        'translate-toolkit',
        'lxml'
    ],
    entry_points='''
        [console_scripts]
        corpus=cli:cli
    ''',
)
