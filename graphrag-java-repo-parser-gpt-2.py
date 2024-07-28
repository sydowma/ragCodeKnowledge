import os
import networkx as nx
from tree_sitter import Language, Parser
import tree_sitter_java as tsjava
import torch
from transformers import RobertaTokenizer, RobertaModel, AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import faiss
import glob
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

# 设置日志
logging.basicConfig(level=logging.INFO)

# 初始化 Tree-sitter
JAVA_LANGUAGE_PATH = 'build/java.so'
if not os.path.exists(JAVA_LANGUAGE_PATH):
    Language.build_library(JAVA_LANGUAGE_PATH, ['tree-sitter-java'])
JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser()
parser.language = JAVA_LANGUAGE

# 初始化编码器
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# 初始化 LLM（这里使用的是 GPT-2，你可以替换为其他模型）
llm_tokenizer = AutoTokenizer.from_pretrained("gpt2")
llm_model = AutoModelForCausalLM.from_pretrained("gpt2")


def parse_java_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        tree = parser.parse(bytes(content, 'utf8'))
        return tree, content
    except Exception as e:
        logging.error(f"Error parsing file {file_path}: {str(e)}")
        return None, None


def process_file(file_path):
    tree, source_code = parse_java_file(file_path)
    if not tree or not source_code:
        return [], []

    nodes = []
    embeddings = []

    for node in tree.root_node.children:
        if node.type in ['method_declaration', 'class_declaration']:
            content = source_code[node.start_byte:node.end_byte]
            nodes.append((file_path, node.type, content))
            embeddings.append(encoder.encode(content))

    return nodes, embeddings


def create_code_index(repo_path):
    java_files = glob.glob(os.path.join(repo_path, "**/*.java"), recursive=True)
    logging.info(f"Found {len(java_files)} Java files in the repository")

    all_nodes = []
    all_embeddings = []

    with ProcessPoolExecutor() as executor:
        future_to_file = {executor.submit(process_file, file_path): file_path for file_path in java_files}
        for future in as_completed(future_to_file):
            nodes, embeddings = future.result()
            all_nodes.extend(nodes)
            all_embeddings.extend(embeddings)

    logging.info(f"Processed {len(all_nodes)} code snippets")

    # 创建 FAISS 索引
    dimension = len(all_embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(numpy.array(all_embeddings))

    return index, all_nodes


def query_code(index, nodes, query, k=5):
    query_vector = encoder.encode([query])
    distances, indices = index.search(query_vector, k)

    results = [nodes[i] for i in indices[0]]
    return results


def generate_response(query, contexts):
    prompt = f"Query: {query}\n\nRelevant code contexts:\n"
    for ctx in contexts:
        prompt += f"\n{ctx[1]}:\n{ctx[2]}\n"
    prompt += "\nBased on the above code contexts, please provide an answer to the query:"

    inputs = llm_tokenizer(prompt, return_tensors="pt")
    outputs = llm_model.generate(**inputs, max_length=200, num_return_sequences=1, no_repeat_ngram_size=2)
    response = llm_tokenizer.decode(outputs[0], skip_special_tokens=True)

    return response


def main():
    repo_path = "path/to/your/java/repository"
    logging.info(f"Processing repository at: {repo_path}")

    index, nodes = create_code_index(repo_path)

    while True:
        query = input("Enter your query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break

        relevant_contexts = query_code(index, nodes, query)
        response = generate_response(query, relevant_contexts)

        print("\nRelevant code snippets:")
        for ctx in relevant_contexts:
            print(f"\n{ctx[0]} - {ctx[1]}:")
            print(ctx[2])

        print("\nGenerated response:")
        print(response)


if __name__ == "__main__":
    main()