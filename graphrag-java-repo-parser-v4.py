import os
import networkx as nx
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
from transformers import RobertaTokenizer, RobertaModel
import torch
from torch.nn.functional import cosine_similarity
import glob
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

# 设置环境变量（如果需要）
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 初始化 Tree-sitter
JAVA_LANGUAGE_PATH = 'build/java.so'

# 如果语言库不存在，则构建它
if not os.path.exists(JAVA_LANGUAGE_PATH):
    Language.build_library(
        JAVA_LANGUAGE_PATH,
        ['tree-sitter-java']
    )

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# 初始化 GraphCodeBERT 编码器
tokenizer = RobertaTokenizer.from_pretrained("microsoft/graphcodebert-base")
model = RobertaModel.from_pretrained("microsoft/graphcodebert-base")


def encode_text(text):
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)


def parse_java_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        tree = parser.parse(bytes(content, 'utf8'))
        return tree, content
    except Exception as e:
        logging.error(f"Error parsing file {file_path}: {str(e)}")
        return None, None


def traverse_tree(tree):
    cursor = tree.walk()

    reached_root = False
    while reached_root == False:
        yield cursor.node

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                retracing = False


def create_code_graph(repo_path):
    G = nx.Graph()
    java_files = glob.glob(os.path.join(repo_path, "**/*.java"), recursive=True)

    for file_path in java_files:
        tree, source_code = parse_java_file(file_path)
        if tree and source_code:
            file_node = file_path
            G.add_node(file_node, type='file', content=source_code)

            for node in traverse_tree(tree):
                if node.type == 'method_declaration':
                    method_name = next(
                        (child.text.decode('utf8') for child in node.children if child.type == 'identifier'), None)
                    if method_name:
                        method_node = f"{file_path}::{method_name}"
                        method_content = source_code[node.start_byte:node.end_byte]
                        G.add_node(method_node, type='method', content=method_content)
                        G.add_edge(file_node, method_node)
                elif node.type == 'class_declaration':
                    class_name = next(
                        (child.text.decode('utf8') for child in node.children if child.type == 'identifier'), None)
                    if class_name:
                        class_node = f"{file_path}::{class_name}"
                        class_content = source_code[node.start_byte:node.end_byte]
                        G.add_node(class_node, type='class', content=class_content)
                        G.add_edge(file_node, class_node)

    logging.info(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G


def query_graph(G, query):
    if G.number_of_nodes() == 0:
        logging.warning("Graph is empty. No nodes to query.")
        return []

    query_embedding = encode_text(query)

    max_similarity = -float('inf')
    most_similar_node = None
    for node, data in G.nodes(data=True):
        node_embedding = encode_text(data['content'])
        similarity = cosine_similarity(query_embedding, node_embedding).item()
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar_node = node

    if most_similar_node is None:
        logging.warning("No similar node found for the query.")
        return []

    context = [G.nodes[most_similar_node]['content']]
    for neighbor in G.neighbors(most_similar_node):
        context.append(G.nodes[neighbor]['content'])

    return context


def main():
    repo_path = "./repo"
    G = create_code_graph(repo_path)

    # 示例查询
    query = "what is event handler？"
    print("start query :", query)
    context = query_graph(G, query)
    print("query result:")

    for i, c in enumerate(context):
        print(f"Context {i + 1}:\n{c}\n")


if __name__ == "__main__":
    main()