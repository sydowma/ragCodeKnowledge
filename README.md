# Java Code Analyzer with RAG and Ollama

This project implements a Java code analyzer that uses Retrieval-Augmented Generation (RAG) techniques combined with the Ollama language model to provide intelligent responses to queries about Java codebases.

## Features

- Parses and indexes Java source code from a specified repository
- Uses Tree-sitter for efficient code parsing
- Implements a RAG (Retrieval-Augmented Generation) system for context-aware code understanding
- Integrates with Ollama for generating human-like responses to code-related queries
- Includes caching mechanisms for improved performance on repeated analyses
- Optimized for handling large codebases with multi-processing capabilities

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7+
- Ollama installed and running locally with the `llama3.1` model
- Git (for cloning the repository)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/sydowma/ragCodeKnowledge.git
   cd ragCodeKnowledge
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure you have the Tree-sitter Java grammar:
   ```
   git clone https://github.com/tree-sitter/tree-sitter-java.git
   ```

## Usage

1. Update the `repo_path` in the script to point to your Java repository:
   ```python
   repo_path = "/path/to/your/java/repository"
   ```

2. Run the script:
   ```
   python optimized_rag_java_analyzer.py
   ```

3. When prompted, enter your query about the Java codebase. For example:
   ```
   Enter your query (or 'quit' to exit): what is xxxx?
   ```

4. The system will retrieve relevant code snippets and generate a response using Ollama.

5. To exit, type 'quit' when prompted for a query.

## How It Works

1. **Code Indexing**: The system parses Java files in the specified repository using Tree-sitter and creates an index of code snippets.

2. **Caching**: Indexed data is cached for faster subsequent runs. The cache is invalidated if the repository content changes.

3. **Query Processing**: When a query is received, the system retrieves relevant code snippets using semantic similarity search.

4. **Response Generation**: Relevant snippets are sent to Ollama along with the query to generate a contextualized response.

## Configuration

You can modify the following parameters in the script:

- `JAVA_LANGUAGE_PATH`: Path to the Tree-sitter Java language file
- `k` in `query_code` function: Number of relevant snippets to retrieve (default is 5)
- Ollama model in `query_ollama` function (default is "deepseek-coder-v2")

## Future Improvements

- Implement incremental updates for the code index
- Add support for other programming languages
- Improve query understanding with more advanced NLP techniques
- Integrate with IDEs or code editors for seamless usage

## Contributing

Contributions to improve the Java Code Analyzer are welcome. Please feel free to submit a Pull Request.


## Contact

If you have any questions or feedback, please open an issue in the GitHub repository.