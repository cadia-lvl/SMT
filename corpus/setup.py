from setuptools import setup

setup(
    name='corpus',
    version='1.0',
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
