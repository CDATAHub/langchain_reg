from setuptools import setup, find_packages

setup(
    name="langchain-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]",
        "python-multipart",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "aiofiles>=23.0.0",
        "websockets>=11.0.0",
        "llama-index>=0.9.0",
        "llama-index-llms-dashscope>=0.1.0",
        "llama-index-embeddings-dashscope>=0.1.0",
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
        "langchain-community>=0.0.10",
        "dashscope>=1.10.0",
        "python-dotenv>=1.0.0",
        "PyPDF2>=3.0.0",
    ],
    python_requires=">=3.11",
)