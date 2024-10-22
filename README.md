# GraphRAG Platform

A powerful Graph-based Retrieval Augmented Generation platform for processing, analyzing, and querying video content using graph databases and large language models.

## 🚀 Features

- **Video Processing Pipeline**
  - Automatic video download and transcription
  - Speaker diarization
  - Code block detection
  - Technical term extraction

- **Advanced Retrieval**
  - Vector-based semantic search
  - Graph traversal queries
  - Hybrid search combining multiple strategies
  - Natural language to Cypher translation

- **Knowledge Graph**
  - Automated relationship extraction
  - Entity recognition
  - Metadata indexing
  - Context-aware querying

- **Multi-Modal Support**
  - Text analysis
  - Audio processing
  - Code understanding
  - Future: Image analysis

## 📋 Prerequisites

- Python 3.9+
- Neo4j Database
- OpenAI API key
- FFmpeg (for audio processing)
- CUDA-compatible GPU (optional, for faster processing)

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/graphrag_platform.git
cd graphrag_platform
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package and development dependencies:
```bash
pip install -e .
pip install -r requirements-dev.txt
```

4. Create a `.env` file with your configuration:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
```

## 🚀 Quick Start

### Basic Usage

```python
from graphrag import GraphRAGConfig, GraphRAGManager

# Initialize configuration
config = GraphRAGConfig(
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="password",
    openai_api_key="your-api-key",
    vector_index_name="video_content"
)

# Create manager instance
manager = GraphRAGManager(config)

# Perform a search
result = await manager.search(
    "What are the key components of GraphRAG?",
    retriever_type="vector"
)

print(result['answer'])
```

### Video Processing

```python
from graphrag_platform.ingestion import VideoProcessor, DatasetManager

# Initialize processors
video_processor = VideoProcessor(output_dir="data")
dataset_manager = DatasetManager("your-dataset-name")

# Process a video
url = "https://youtube.com/watch?v=your-video-id"
metadata, segments = await video_processor.process_video(url)

# Add to dataset
await dataset_manager.add_video(metadata, segments)
```

## 🔍 Retrieval Strategies

### 1. Vector Search
Best for semantic similarity and concept understanding:
```python
result = await manager.search(
    "Explain vector embeddings",
    retriever_type="vector"
)
```

### 2. Graph Traversal
Ideal for exploring relationships and connected information:
```python
result = await manager.search(
    "What topics are related to GraphRAG?",
    retriever_type="vector_cypher"
)
```

### 3. Hybrid Search
Combines keyword matching with semantic search:
```python
result = await manager.search(
    "Find tutorials about Neo4j",
    retriever_type="hybrid"
)
```

## 🐳 Docker Support

Build and run using Docker:

```bash
# Build image
docker build -t graphrag-platform .

# Run container
docker run -d \
  --name graphrag \
  -e NEO4J_URI=bolt://neo4j:7687 \
  -e NEO4J_USERNAME=neo4j \
  -e NEO4J_PASSWORD=password \
  -e OPENAI_API_KEY=your-key \
  graphrag-platform
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=graphrag_platform
```

## 🔧 Configuration Options

### GraphRAG Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `neo4j_uri` | Neo4j database URI | - |
| `neo4j_username` | Neo4j username | - |
| `neo4j_password` | Neo4j password | - |
| `openai_api_key` | OpenAI API key | - |
| `vector_index_name` | Name of vector index | - |
| `fulltext_index_name` | Name of fulltext index | None |
| `embedding_model` | Model for embeddings | "text-embedding-3-large" |
| `llm_model` | Language model | "gpt-4-turbo-preview" |
| `temperature` | LLM temperature | 0 |
| `top_k` | Number of results | 5 |

## 📚 Project Structure

```
graphrag_platform/
├── graphrag/               # Core GraphRAG implementation
├── ingestion/             # Video processing and dataset management
├── agents/                # Agent system for query routing
├── tests/                # Test suite
└── main.py               # Entry point
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Neo4j](https://neo4j.com/) for graph database support
- [OpenAI](https://openai.com/) for language models
- [Whisper](https://github.com/openai/whisper) for speech recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video downloading

## 📮 Contact

For questions and support, please open an issue in the GitHub repository.
