#!/usr/bin/env python
# coding=utf-8
from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    readme = f.read()

with open('LICENSE', encoding='utf-8') as f:
    license = f.read()

with open('requirements.txt', encoding='utf-8') as f:
    reqs = f.read()

setup(
    name='fastchatgpt',
    version='0.0.3',
    description='fastchatgpt: A tool to interact with large language model(LLM)',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='Apache license',
    python_requires='>=3.6',
    include_package_data=True,
    packages=find_packages(),
    install_requires=reqs.strip().split('\n'),
    entry_points={
        'console_scripts':[
            # 'bot_evaluate = fastchatgpt.__main__:bot_evaluate',
            # 'bot_infer = fastchatgpt.__main__:bot_infer',
            'bot_play = fastchatgpt.__main__:bot_play',
        ]
    }
)
