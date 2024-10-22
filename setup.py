# setup.py
from setuptools import setup, find_packages

setup(
    name="graphrag-platform",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "neo4j-graphrag",
        "openai",
        "yt-dlp",
        "whisper",
        "datasets",
        "transformers",
        "langchain",
        "fastapi",
        "celery",
        "redis",
        "pydantic",
        "pytest",
        "pytest-asyncio",
    ],
    python_requires=">=3.9",
)
