from setuptools import setup, find_packages

setup(
    name="crypto_bot",
    version="1.0",
    description="Simple crypto bot",
    author="Christopher Nathan",
    author_email="christophernathan1217@gmail.com",
    url="https://github.com/christophernathan/crypto_bot",
    packages=find_packages(include=['bot','bot.*']),
    install_requires=[
        'requests', 'requests-mock', 'python-dotenv', 'pandas', 'pytest'
    ],
    entry_points={
        "console_scripts": [
            "bot = bot.__main__:bot"
        ]
    },
)