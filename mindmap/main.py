import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# 下载必要的NLTK数据
nltk.download('punkt', quiet=True)

# 初始化模型
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device="mps")


def extract_topics_and_key_sentences(text, num_topics=3):
    # 使用BART模型进行摘要生成
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']

    # 将文本分割成句子
    sentences = sent_tokenize(text)

    # 使用TF-IDF向量化句子
    vectorizer = TfidfVectorizer(stop_words='english')
    sentence_vectors = vectorizer.fit_transform(sentences)

    # 使用K-means聚类来提取主题
    kmeans = KMeans(n_clusters=num_topics)
    kmeans.fit(sentence_vectors)

    # 找出每个簇的中心句子作为主题
    closest_indices = []
    for i in range(num_topics):
        distances = np.linalg.norm(sentence_vectors - kmeans.cluster_centers_[i], axis=1)
        closest_index = np.argmin(distances)
        closest_indices.append(closest_index)

    topics = [sentences[i] for i in closest_indices]

    # 选择与主题最相似的句子作为关键句子
    key_sentences = []
    for topic in topics:
        similarities = sentence_vectors.dot(vectorizer.transform([topic]).T).toarray().flatten()
        key_sentence_index = np.argmax(similarities)
        key_sentences.append(sentences[key_sentence_index])

    return topics, key_sentences, summary


def clean_text_for_mermaid(text):
    # 移除换行符和多余的空格
    cleaned = ' '.join(text.split())
    # 转义特殊字符
    cleaned = cleaned.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return cleaned


def generate_mindmap_mermaid(text):
    # 提取主题、关键句子和摘要
    topics, key_sentences, summary = extract_topics_and_key_sentences(text)

    # 生成正确的Mermaid语法的思维导图
    mermaid_syntax = ["```mermaid", "mindmap"]
    mermaid_syntax.append("  root((Artificial Intelligence))")
    mermaid_syntax.append(f"    Summary[{clean_text_for_mermaid(summary)}]")

    for i, (topic, key_sentence) in enumerate(zip(topics, key_sentences), 1):
        topic_clean = clean_text_for_mermaid(topic)
        key_sentence_clean = clean_text_for_mermaid(key_sentence)
        mermaid_syntax.append(f"    Topic {i}[{topic_clean}]")
        mermaid_syntax.append(f"      Key Point[{key_sentence_clean}]")

    mermaid_syntax.append("```")
    return "\n".join(mermaid_syntax)


def extract_key_points(text, num_points=5):
    sentences = sent_tokenize(text)
    vectorizer = TfidfVectorizer(stop_words='english')
    sentence_vectors = vectorizer.fit_transform(sentences)

    kmeans = KMeans(n_clusters=num_points)
    kmeans.fit(sentence_vectors)

    closest_indices = []
    for i in range(num_points):
        distances = np.linalg.norm(sentence_vectors - kmeans.cluster_centers_[i], axis=1)
        closest_index = np.argmin(distances)
        closest_indices.append(closest_index)

    key_points = [sentences[i] for i in closest_indices]
    return key_points

def generate_flowchart(text):
    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
    key_points = extract_key_points(text)

    mermaid_syntax = ["```mermaid", "flowchart TD"]
    mermaid_syntax.append(f"    A[{clean_text_for_mermaid(summary)}]")

    for i, point in enumerate(key_points, 1):
        mermaid_syntax.append(f"    A --> B{i}[{clean_text_for_mermaid(point)}]")

    mermaid_syntax.append("```")
    return "\n".join(mermaid_syntax)


def generate_sequence_diagram(text):
    key_points = extract_key_points(text, num_points=4)  # 减少点数以简化时序图

    mermaid_syntax = ["```mermaid", "sequenceDiagram"]
    mermaid_syntax.append("    participant Human")
    mermaid_syntax.append("    participant AI")

    for i, point in enumerate(key_points, 1):
        if i % 2 == 1:
            mermaid_syntax.append(f"    Human->>AI: Step {i}")
        else:
            mermaid_syntax.append(f"    AI->>Human: {clean_text_for_mermaid(point)}")

    mermaid_syntax.append("```")
    return "\n".join(mermaid_syntax)

# 示例使用
sample_text = """
Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans. AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.
The term "artificial intelligence" had previously been used to describe machines that mimic and display "human" cognitive skills that are associated with the human mind, such as "learning" and "problem-solving". This definition has since been rejected by major AI researchers who now describe AI in terms of rationality and acting rationally, which does not limit how intelligence can be articulated.
AI applications include advanced web search engines, recommendation systems, understanding human speech, self-driving cars, automated decision-making and competing at the highest level in strategic game systems. As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology.
"""

mermaid_mindmap = generate_mindmap_mermaid(sample_text)
print(mermaid_mindmap)


print("Flowchart:")
print(generate_flowchart(sample_text))
print("\nSequence Diagram:")
print(generate_sequence_diagram(sample_text))