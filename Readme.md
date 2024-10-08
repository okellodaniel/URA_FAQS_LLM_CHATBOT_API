# URA FAQs LLM Powered Chatbot API
___
Taxpayers in Uganda face difficulties accessing clear and organized tax information because the FAQs on the Uganda Revenue Authority (URA) website are scattered and unstructured. This project addresses the problem by developing a chatbot powered by Retrieval-Augmented Generation (RAG) using the scraped URA FAQs. The chatbot, communicating with GPT-4O-mini, will provide precise and immediate answers to users' tax-related questions, enhancing access to essential tax information.


### Overview
This project is a URA FAQ Chatbot API powered by Retrieval-Augmented Generation (RAG), Elasticsearch, and OpenAI GPT models. It includes a web scraping script that updates FAQs from the URA website, with all data stored in PostgreSQL. Grafana is used for system monitoring.

It embeds the following key features
1. Hybrid,text,vector search: Combining, and retaining keyword and vector search in Elasticsearch for accurate FAQ retrieval.
2. RAG: Generates natural language responses using GPT models based on retrieved FAQs.
3. Web Scraping: Automatically updates the FAQ database with data from the URA website.
4. Feedback System: Stores user feedback in PostgreSQL for improving response quality.
5. Django API: Provides endpoints for chatbot interactions, feedback, and history management.
6. Grafana: Monitors system metrics, including API usage and Elasticsearch health.
7. Dockerized: All components run in Docker containers for scalability and easy deployment.

This chatbot delivers accurate, up-to-date responses and offers real-time performance monitoring, making it a scalable and automated solution for URA FAQs.
![alt text](./misc/postman.png)
___

### Dataset
This dataset contains a collection of FAQs scraped from the URA (https://ura.go.ug/en/general-faqs/) website. It includes the following fields:

- Question: A frequently asked question from URA's public users.
- Answer: The official response provided by URA.
- Section: The category under which the FAQ falls, such as "Import & Export FAQs," "Domestic Taxes FAQs," "Processes & Systems FAQs," and "General FAQs."

The dataset provides a structured collection of questions and answers across various tax-related topics and processes. Each entry is organized to help users quickly access important URA information.
___

### Technologies
- Python 3.12
- Docker and Docker Compose for containerization
- ElasticSearch for text,vector and hybrid search
- Django Rest Framework and Django as the API interface (see Background for more information on Flask)
- Grafana for monitoring and PostgreSQL as the datasource
- OpenAI as the LLM
___

### Getting Started
1. Clone the repository
```bash
git clone <repository-url>
cd <repository-directory>

```
2. Setup a virtual environment for the project
```bash
python3 -m venv venv
source venv/bin/activate  # For Linux/Mac
# or
venv\Scripts\activate  # For Windows

```
 
3. Install requirements
```bash
pip install -r requirements.txt
```
4. Build the docker containers
```bash
docker-compose up --build

```
5. Create a .env file and populate it with the details below
```txt
# Postgres Configuration
POSTGRES_HOST=localhost
POSTGRES_DB=ura_faqs
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432

# ElasticSearch Configuration
ELASTIC_URL_LOCAL=http://localhost:9200
ELASTIC_URL=http://elasticsearch:9200
ELASTIC_PORT=9200

#Other Configuration
MODEL_NAME=multi-qa-MiniLM-L6-cos-v1
INDEX_NAME=ura_faqs

OPENAI_API_KEY=<Your-open-ai-key>
```
6. Install Postman
- [Download](https://dl.pstmn.io/download/latest/)
- Once installed, navigate to the misc folder of the project and import the `URA FAQS RAG Project.postman_collection.json` file into Postman to test the API endpoints.

___
### Code
The application codebase resides in the URA_RAG folder. The application structure is as follows
#### app
The django Rest Framework application API. This contains
- [models.py](./app/rag/models.py) - Database models representing the conversation and feedback models.
- [raglogic.py](./app/rag/raglogic.py) - RAG logic of the project
- [services.py](./app/rag/services.py) - Acts as an ORM for the interaction between the views and the database layer
- [views.py](./app/rag/views.py) - The views contain the API routes
#### notebooks
- [evaluation.ipynb](./notebooks/evaluation.ipynb) - Contains logic for evaluating the RAG application
- [ground_truth.ipynb](./notebooks/ground_truth.ipynb) - Contains logic used in generating the ground truth dataset

#### scripts
- [scrapper.py](.scrapper.py) - Contains the logic for scrapping FAQ data off the URA website
___
### Running Application

The application functionality is currently set to run locally on (bare metal), starting with installing the application requirements, the neccessary files required, and running the dockerised application 
___
### Retrieval evaluation
For retrieval evaluation,below are the metrics 
- Hit Rate: 89.47%
- Mean Reciprocal Rank (MRR): 76.81%
- Recall @ k: 89.47%
- Normalized Discounted Cumulative Gain (NDCG @ k): 0.00%
- Precision @ k: 17.89%
___
### RAG flow evaluation
#### LLM-as-a-Judge
LLM as a judge was used to evaluate the quality of the RAG flow. 2 models were used for this purpose i.e.
- gpt-4o-mini: Sampled 200 faqs
- gpt-3.5-turbo: Sampled 200 faqs

**gpt-3.5-turbo**
- 89(44.5%) RELEVANT
- 87 (43.5%) PARTLY_RELEVANT
- 24 (12%) NON_RELEVANT

**gpt-4o-mini**
- 175(87.5%) RELEVANT
- 19 (9.5%) PARTLY_RELEVANT
- 8 (3.0%) NON_RELEVANT

#### Cosine similarity

Cosine similarity was also used to evaluate the rag performance.

![alt text](./misc/Cosine_similarity.png) 

This graph represents the distribution of cosine similarities between the original answers (A) and the regenerated answers (A') for two different language models (LLMs) gpt-3.5-turbo represented in blue and gpt-4o-mini (represented in orange). 

Key insights include;
- Both models showed a similar distribution, with a peak around the 0.7 to 0.8 range. This indicated that for the majority of cases, both models generated responses that were highly similar to the original answers (high cosine similarity).
- Both curves peaked around 0.7 - 0.8, meaning most answers were closely related to their original counterparts.
- GPT-4o-mini had a slightly higher peak, showing more frequent high-similarity answers compared to GPT-3.5-turbo.
- GPT-4o-mini had a slightly higher mean cosine similarity (0.699) compared to GPT-3.5-turbo (0.683), indicating that, on average, GPT-4o-mini generated answers that were more similar to the original ones.
- Both models performed well in generating similar answers to the original, with cosine similarities clustering around 0.7 to 0.8.
- GPT-4o-mini demonstrated slightly better performance in terms of generating closer matches to the original answers, with a higher mean and more consistent results (lower variance).
- GPT-3.5-turbo showed more variance and outliers, indicating that while it performs well on average, some of its answers deviate more significantly from the original answers.
___
### Monitoring
![alt text](./misc/image.png)

1. Total Conversations Over Time is presented as a Time-series graph that displays the number of conversations over time.
It is powered by a query that counts the number of faqs in the over time intervals.

```sql
SELECT
  date_trunc('hour', timestamp) AS "time",
  COUNT(*) AS "conversations"
FROM
  rag_conversation
WHERE
  timestamp BETWEEN $__timeFrom() AND $__timeTo()
GROUP BY
  "time"
ORDER BY
  "time"

```
2. Average Response Time Over Time is presented as a time-series graph thatshows how response times vary over time.It is powered by a query that aggregates the response_time field over time intervals.

```sql
SELECT
  date_trunc('hour', timestamp) AS "time",
  AVG(response_time) AS "avg_response_time"
FROM
  rag_conversation
WHERE
  timestamp BETWEEN $__timeFrom() AND $__timeTo()
GROUP BY
  "time"
ORDER BY
  "time"

```
3. Total OpenAI Cost Over Time Is a single Stat panel that displays the total cost incurred for using OpenAI's services over the selected time range. It provides insight into your expenditure.

```sql
SELECT
  SUM(openai_cost) AS "total_cost"
FROM
  rag_conversation
WHERE
  timestamp BETWEEN $__timeFrom() AND $__timeTo()

```
4. Relevance Distribution,presented as a Pie chart that visualizes the distribution of relevance levels in your conversations. It helps you understand how relevant your responses are according to your evaluation criteria.

```sql
SELECT
  relevance,
  COUNT(*) AS "count"
FROM
  rag_conversation
WHERE
  timestamp BETWEEN $__timeFrom() AND $__timeTo()
GROUP BY
  relevance

```
5. Feedback Summary Is represented as a Bar chart that summarizes the number of positive and negative feedback entries. This panel allows you to gauge user satisfaction levels and identify areas for improvement.

```sql
SELECT
  CASE
    WHEN feedback = 1 THEN 'Positive'
    WHEN feedback = -1 THEN 'Negative'
    ELSE 'Neutral'
  END AS "feedback_type",
  COUNT(*) AS "count"
FROM
  rag_feedback
WHERE
  timestamp BETWEEN $__timeFrom() AND $__timeTo()
GROUP BY
  "feedback_type"

```
6. Conversations Per Model Used is presented as a Bar chart that compares the number of conversations per model (e.g., GPT-3.5, GPT-4). It helps you analyze the usage and popularity of different models.

```sql
SELECT
  model_used,
  COUNT(*) AS "conversations"
FROM
  rag_conversation
WHERE
  timestamp BETWEEN $__timeFrom() AND $__timeTo()
GROUP BY
  model_used
ORDER BY
  "conversations" DESC

```
7. Average Response Time by Model is presented as a Bar chart that shows the average response time for each model used. This panel helps you assess which models are more efficient in terms of response time.

```sql
SELECT
  model_used,
  AVG(response_time) AS "avg_response_time"
FROM
  rag_conversation
WHERE
  timestamp BETWEEN $__timeFrom() AND $__timeTo()
GROUP BY
  model_used
ORDER BY
  "avg_response_time" ASC

```
