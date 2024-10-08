import json
import logging
import os
import time

from openai import OpenAI
from typing import Any, Dict, List, Tuple
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)  # Set to INFO for detailed logs
logger = logging.getLogger(__name__)

ELASTIC_URL = os.getenv("ELASTIC_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

# Initialize Elasticsearch and OpenAI
es_client = Elasticsearch(ELASTIC_URL)

model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")

client = OpenAI(api_key=OPENAI_API_KEY)


logger.info("Initialized Elasticsearch client and OpenAI API.")

def elastic_search_text(query: str, index_name: str = INDEX_NAME) -> List[Dict[str, Any]]:
    """
    Perform a text-based search on Elasticsearch.
    """
    logger.info(f"Starting text-based search for query: {query}")
    
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question", "answer", "section"],
                        "type": "best_fields",
                    }
                }
            }
        },
    }

    try:
        response = es_client.search(index=index_name, body=search_query)
        results = [hit["_source"] for hit in response["hits"]["hits"]]
        logger.info(f"Found {len(results)} results for text-based search.")
        return results
    except Exception as e:
        logger.error(f"Error in text-based search: {e}")
        return []

def elastic_search_hybrid(
    field: str, query: str, 
    query_vector: List[float], 
    index_name: str = INDEX_NAME
) -> List[Dict[str, Any]]:
    """
    Perform a hybrid search (keyword and KNN) on Elasticsearch.
    """
    logger.info(f"Starting hybrid search for query: {query} with vector.")

    knn_query = {
        "field": field,
        "query_vector": query_vector,
        "k": 5,
        "num_candidates": 10000,
        "boost": 0.5,
    }

    keyword_query = {
        "bool": {
            "must": {
                "multi_match": {
                    "query": query,
                    "fields": ["question", "answer", "section"],
                    "type": "best_fields",
                    "boost": 0.5,
                }
            },
        }
    }

    search_query = {
        "knn": knn_query,
        "query": keyword_query,
        "size": 5,
        "_source": ["answer", "section", "question","id"],
    }

    try:
        es_results = es_client.search(index=index_name, body=search_query)
        results = [hit["_source"] for hit in es_results["hits"]["hits"]]
        logger.info(f"Found {len(results)} results for hybrid search.")
        return results
    except Exception as e:
        logger.error(f"Error during hybrid search: {e}")
        return []

def elastic_search_knn(
    field: str, vector: List[float], index_name: str = INDEX_NAME
) -> List[Dict[str, Any]]:
    """
    Perform a KNN search on Elasticsearch.
    """
    logger.info(f"Starting KNN search on field: {field} with vector.")

    knn = {
        "field": field,
        "query_vector": vector,
        "k": 5,
        "num_candidates": 10000,
    }

    search_query = {
        "knn": knn,
        "_source": ["answer", "section", "question", "id"],
    }

    try:
        es_results = es_client.search(index=index_name, body=search_query)
        results = [hit["_source"] for hit in es_results["hits"]["hits"]]
        logger.info(f"Found {len(results)} results for KNN search.")
        return results
    except Exception as e:
        logger.error(f"Error during KNN search: {e}")
        return []

def build_prompt(query: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the language model based on the query and search results.
    """
    logger.info(f"Building prompt for query: {query}")

    context = "\n\n".join(
        [
            f"section: {faq['section']}\nquestion: {faq['question']}\nanswer: {faq['answer']}"
            for faq in search_results
        ]
    )
    
    prompt_template = (
        "You're a Uganda Revenue Authority (URA) Expert. Answer the QUESTION based on the CONTEXT from the FAQ database.\n"
        "Use only the facts from the CONTEXT when answering the QUESTION.\n\n"
        "QUESTION: {question}\n\n"
        "CONTEXT:\n{context}"
    )
    
    prompt = prompt_template.format(question=query, context=context).strip()
    logger.debug(f"Built prompt: {prompt}")
    return prompt

def llm(prompt: str, model_choice: str) -> Tuple[str, Dict[str, int], float]:
    """
    Call the language model with the given prompt and model choice.
    """
    logger.info(f"Sending prompt to language model: {model_choice}")
    start_time = time.time()

    try:
        if model_choice.startswith("openai/"):
            model_name = model_choice.split("/")[-1]
            response = client.chat.completions.create(
                model=model_name, 
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content
            tokens = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            response_time = time.time() - start_time
            logger.info(f"LLM returned an answer in {response_time:.2f} seconds.")
            return answer, tokens, response_time
        else:
            raise ValueError(f"Unknown model choice: {model_choice}")
    except Exception as e:
        logger.error(f"Error while calling LLM: {e}")
        raise

def evaluate_relevance(question: str, answer: str) -> Tuple[str, str, Dict[str, int]]:
    """
    Evaluate the relevance of the generated answer to the question.
    """
    logger.info(f"Evaluating relevance of answer for question: {question}")

    prompt_template = (
        'You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.\n'
        'Your task is to analyze the relevance of the generated answer to the given question.\n'
        'Based on the relevance of the generated answer, you will classify it\n'
        'as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".\n\n'
        "Here is the data for evaluation:\n\n"
        "Question: {question}\n"
        "Generated Answer: {answer}\n\n"
        "Please analyze the content and context of the generated answer in relation to the question\n"
        "and provide your evaluation in parsable JSON without using code blocks:\n\n"
        '{{\n  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",\n  '
        '"Explanation": "[Provide a brief explanation for your evaluation]"\n}}'
    )

    prompt = prompt_template.format(question=question, answer=answer)
    evaluation, tokens, _ = llm(prompt, "openai/gpt-4o-mini")

    try:
        json_eval = json.loads(evaluation)
        logger.info(f"Evaluation returned relevance: {json_eval['Relevance']}")
        return json_eval["Relevance"], json_eval["Explanation"], tokens
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON evaluation: {e}")
        return "UNKNOWN", "Failed to parse evaluation", tokens

def calculate_openai_cost(model_choice: str, tokens: Dict[str, int]) -> float:
    """
    Calculate the cost of the OpenAI API call.
    """
    logger.info(f"Calculating cost for model {model_choice}")

    if model_choice == "openai/gpt-3.5-turbo":
        openai_cost = (
            tokens["prompt_tokens"] * 0.0015 + tokens["completion_tokens"] * 0.002
        ) / 1000
    elif model_choice in ["openai/gpt-4o", "openai/gpt-4o-mini"]:
        openai_cost = (
            tokens["prompt_tokens"] * 0.03 + tokens["completion_tokens"] * 0.06
        ) / 1000
    else:
        openai_cost = 0.0

    logger.info(f"OpenAI cost: ${openai_cost:.4f}")
    return openai_cost

def get_answer(
    query: str,
    model_choice: str,
    search_type: str,
    index_name: str = INDEX_NAME,
) -> Dict[str, Any]:
    """
    Get an answer to the query using the specified model and search type.
    """
    logger.info(f"Fetching answer for query: {query} with model: {model_choice} and search type: {search_type}")
    
    try:
        if search_type == "vector":
            vector = model.encode(query).tolist()
            search_results = elastic_search_knn("question_text_vector",vector, index_name)
        elif search_type == "text":
            search_results = elastic_search_text(query, index_name)
        else:
            search_results = elastic_search_hybrid("question_answer_vector", query, index_name)

        prompt = build_prompt(query, search_results)
        answer, tokens, response_time = llm(prompt, model_choice)
        relevance, explanation, eval_tokens = evaluate_relevance(query, answer)
        openai_cost = calculate_openai_cost(model_choice, tokens)

        logger.info(f"Answer generated for query: {query}")

        return {
            "answer": answer,
            "response_time": response_time,
            "relevance": relevance,
            "relevance_explanation": explanation,
            "model_used": model_choice,
            "prompt_tokens": tokens["prompt_tokens"],
            "completion_tokens": tokens["completion_tokens"],
            "total_tokens": tokens["total_tokens"],
            "eval_prompt_tokens": eval_tokens["prompt_tokens"],
            "eval_completion_tokens": eval_tokens["completion_tokens"],
            "eval_total_tokens": eval_tokens["total_tokens"],
            "openai_cost": openai_cost,
        }
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return {"error": "An error occurred while fetching the answer."}