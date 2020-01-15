import setuptools
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='frontend',
    version='2.1.3',
    author='Haukur Páll Jónsson',
    author_email='haukurpalljonsson@gmail.com',
    url='https://github.com/cadia-lvl/SMT/tree/master/frontend',
    description='A frontend to Moses SMT and a collection of tools to process text.',
    license='MIT',
    python_requires='>=3.7.*',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'sacremoses',
        'tokenizer==2.0.3',
        'translate-toolkit',
        'lxml',
        'tqdm',
        'aiohttp-xmlrpc',
        'flask',
        'flask-restful',
        'flask-cors'
    ],
    entry_points='''
        [console_scripts]
        frontend=frontend.cli:cli
    ''',
)
