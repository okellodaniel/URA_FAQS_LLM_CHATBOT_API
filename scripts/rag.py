import json
import pandas as pd
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

# Configuration
MODEL_NAME = "multi-qa-MiniLM-L6-cos-v1"
ES_URL = 'http://localhost:9200'
INDEX_NAME = "ura_faqs"
INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "question": {"type": "text"},
            "answer": {"type": "text"},
            "section": {"type": "text"},
            "question_vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            },
            "answer_vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            },
            "question_answer_vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

# Load FAQ Data
def load_faqs(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

# Initialize SentenceTransformer model
def initialize_model(model_name):
    return SentenceTransformer(model_name)

# Vectorize FAQ data (with concatenated question + answer for question_answer_vector)
def vectorize_faqs(faqs, model):
    for faq in tqdm(faqs, desc="Vectorizing FAQs"):
        question = faq['question']
        answer = faq['answer']
        qa = question + ' ' + answer

        # Generate vectors for question, answer, and concatenated question + answer
        faq['question_vector'] = model.encode(question)
        faq['answer_vector'] = model.encode(answer)
        faq['question_answer_vector'] = model.encode(qa)
    return faqs

# Initialize Elasticsearch
def initialize_es(es_url):
    es_client = Elasticsearch(es_url)
    if not es_client.ping():
        raise ValueError("Elasticsearch is not running.")
    return es_client

# Create Elasticsearch Index
def create_index(es_client, index_name, settings):
    es_client.indices.delete(index=index_name, ignore_unavailable=True)
    es_client.indices.create(index=index_name, body=settings)

# Index FAQs to Elasticsearch
def index_faqs(es_client, faqs, index_name):
    for faq in tqdm(faqs, desc="Indexing FAQs"):
        es_client.index(index=index_name, document=faq)

# Perform hybrid search (KNN + Keyword)
def elastic_search_hybrid(es_client, field, query, query_vector, index_name="ura_faqs"):
    search_query = {
        "knn": {
            "field": field,
            "query_vector": query_vector,
            "k": 5,
            "num_candidates": 10000,
            "boost": 0.5
        },
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question", "answer", "section"],
                        "type": "best_fields",
                        "boost": 0.5
                    }
                }
            }
        },
        "size": 5,
        "_source": ["question", "answer", "section", "id"]
    }

    try:
        es_results = es_client.search(index=index_name, body=search_query)
        results = [hit['_source'] for hit in es_results['hits']['hits']]
        return [{"question": res["question"], "answer": res["answer"], "section": res["section"]} for res in results]
    except Exception as e:
        print(f"Error during hybrid search: {e}")
        return []

# Helper function to search FAQs
def faq_question(es_client, model, question):
    question_vector = model.encode(question)
    return elastic_search_hybrid(es_client, "question_answer_vector", question, question_vector, index_name=INDEX_NAME)

# Main function
def main():
    # Load and Vectorize FAQs
    faqs = load_faqs('../data/faqs-with-ids.json')
    model = initialize_model(MODEL_NAME)
    faqs = vectorize_faqs(faqs, model)

    # Initialize Elasticsearch
    es_client = initialize_es(ES_URL)

    # Create index and index FAQs
    create_index(es_client, INDEX_NAME, INDEX_SETTINGS)
    index_faqs(es_client, faqs, INDEX_NAME)

    # Search for a FAQ
    result = faq_question(es_client, model, "What is a TIN?")
    print(result)

if __name__ == "__main__":
    main()
