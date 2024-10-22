# setup.py
from setuptools import setup, find_packages

setup(
    name="graphrag-platform",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "neo4j-graphrag>=1.0.0",
        "openai>=1.51.2",
        "yt-dlp>=2024.3.1",
        "whisper>=1.1.10",
        "datasets>=2.18.0",
        "transformers>=4.38.2",
        "langchain>=0.1.9",
        "fastapi>=0.110.0",
        "celery>=5.3.6",
        "redis>=5.0.1",
        "pydantic>=2.6.3",
        "pytest>=8.0.2",
        "pytest-asyncio>=0.23.5"
    ],
    python_requires=">=3.9",
)
