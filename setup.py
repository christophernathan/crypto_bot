from setuptools import setup, find_packages
from bot.__main__ import bot

setup(
    name="crypto_bot",
    author="Christopher Nathan",
    author_email="christophernathan1217@gmail.com",
    version="1.0",
    packages=find_packages('bot', exclude=['mocks','test','utils']),
    entry_points={
        "console_scripts": [
            "bot = bot.__main__:bot"
        ]
    },
)