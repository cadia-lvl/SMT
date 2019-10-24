from setuptools import setup

setup(
    name='corpus',
    version='0.1',
    py_modules=['yourscript'],
    install_requires=[
        'Click',
        'nltk',
        'tokenizer',
        'translate-toolkit',
        'lxml'
    ],
    entry_points='''
        [console_scripts]
        corpus=corpus:cli
    ''',
)
