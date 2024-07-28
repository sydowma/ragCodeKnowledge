import os
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
import glob
import logging
import requests
import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import hashlib
from concurrent.futures import ProcessPoolExecutor
import time

# 设置日志
logging.basicConfig(level=logging.INFO)

# 初始化 Tree-sitter
JAVA_LANGUAGE_PATH = 'build/java.so'
if not os.path.exists(JAVA_LANGUAGE_PATH):
    Language.build_library(JAVA_LANGUAGE_PATH, ['tree-sitter-java'])

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# 初始化句子编码器
encoder = SentenceTransformer('all-MiniLM-L6-v2')


def parse_java_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        tree = parser.parse(bytes(content, 'utf8'))
        return tree, content
    except Exception as e:
        logging.error(f"Error parsing file {file_path}: {str(e)}")
        return None, None


def extract_code_snippets(tree, source_code):
    snippets = []
    for node in tree.root_node.children:
        if node.type in ['method_declaration', 'class_declaration']:
            snippet = source_code[node.start_byte:node.end_byte]
            snippets.append(snippet)
    return snippets


def process_file(file_path):
    tree, source_code = parse_java_file(file_path)
    if tree and source_code:
        return extract_code_snippets(tree, source_code)
    return []


def compute_repo_hash(repo_path):
    hasher = hashlib.md5()
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                hasher.update(file_path.encode())
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
    return hasher.hexdigest()


def load_or_create_index(repo_path, force_rebuild=False):
    repo_hash = compute_repo_hash(repo_path)
    cache_file = f'code_index_cache_{repo_hash}.pkl'

    if os.path.exists(cache_file) and not force_rebuild:
        logging.info("Loading cached index...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)

    logging.info("Creating new index...")
    all_snippets = []
    java_files = glob.glob(os.path.join(repo_path, "**/*.java"), recursive=True)

    # 使用多进程处理文件
    with ProcessPoolExecutor() as executor:
        snippets_list = list(executor.map(process_file, java_files))
        all_snippets = [snippet for sublist in snippets_list for snippet in sublist]

    logging.info(f"Extracted {len(all_snippets)} code snippets")

    # 编码代码片段
    embeddings = encoder.encode(all_snippets)

    # 创建 FAISS 索引
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # 缓存索引
    with open(cache_file, 'wb') as f:
        pickle.dump((index, all_snippets), f)

    return index, all_snippets


def query_code(index, all_snippets, query, k=5):
    query_vector = encoder.encode([query])
    distances, indices = index.search(query_vector, k)
    return [all_snippets[i] for i in indices[0]]


def query_ollama(prompt, model="llama3.1"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return json.loads(response.text)['response']
    else:
        logging.error(f"Error querying Ollama: {response.status_code}")
        return None


def main():
    repo_path = "./repo"

    start_time = time.time()
    index, all_snippets = load_or_create_index(repo_path)
    logging.info(f"Index loading/creation took {time.time() - start_time:.2f} seconds")

    while True:
        query = input("Enter your query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break

        start_time = time.time()
        relevant_snippets = query_code(index, all_snippets, query)
        logging.info(f"Code retrieval took {time.time() - start_time:.2f} seconds")

        if not relevant_snippets:
            print("No relevant code found.")
            continue

        logging.info("Generating response with Ollama...")
        prompt = f"Query: {query}\n\nRelevant code contexts:\n"
        for i, snippet in enumerate(relevant_snippets):
            prompt += f"\nSnippet {i + 1}:\n{snippet}\n"
        prompt += "\nBased on the above code snippets, please provide a detailed answer to the query."

        start_time = time.time()
        response = query_ollama(prompt)
        logging.info(f"Ollama response generation took {time.time() - start_time:.2f} seconds")

        if response:
            print("\nGenerated response:")
            print(response)
        else:
            print("Failed to generate a response.")


if __name__ == "__main__":
    main()