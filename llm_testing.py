# import modules
import json
import boto3

from typing import Any
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.embeddings.bedrock import BedrockEmbeddings
from langchain.globals import set_debug, set_verbose
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_elasticsearch import ElasticsearchStore
from langchain.llms.bedrock import Bedrock
from elasticsearch import Elasticsearch
import requests

def create_vector_store(es):
    bedrock_client = boto3.client(
        service_name="bedrock-runtime", region_name="us-east-1")
    embeddings = BedrockEmbeddings(client=bedrock_client)

   # es_instance = Elasticsearch(hosts="http://localhost:9200",connections_per_node=5,request_timeout=600.0)

    vector_store = ElasticsearchStore(
        es_connection=es,
        index_name="my_documents",
        embedding=embeddings,
        strategy=ElasticsearchStore.SparseVectorRetrievalStrategy(),
    )

    with open('data.json', 'rt') as f:
        documents = json.loads(f.read())
        for doc in documents:
            url = doc['download_url']
            response = requests.get(url)
            doc['page_content'] = str(response.content)

    metadata = []
    content = []
    for doc in documents:
        doc_content = str(doc['page_content'])
        content.append(doc_content)
        metadata.append(
            {
                "name": doc["name"],
            }
        )
        
    print("Read documents from data.json!!!")
    
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=512, chunk_overlap=256
    )
    docs = text_splitter.create_documents(content, metadatas=metadata)
    
    print("Created documents : ", len(docs))
    
    vector_store.from_documents(
        documents=docs,
        es_connection=es,
        index_name="my_documents",
        strategy=ElasticsearchStore.SparseVectorRetrievalStrategy(),
    )
    print("Ingested documents into vector store!!!")

    default_model_id = "anthropic.claude-v2:1"
    llm = Bedrock(client=bedrock_client, model_id=default_model_id)
    
    print("Connected to Bedrock client!!!")

    retriever = vector_store.as_retriever()
    qa = RetrievalQA.from_llm(llm=llm, retriever=retriever,
                              return_source_documents=True)
    print("Created a retrieval QA system!!!")
    return qa


def run_llm_test(qa, question: str) -> dict[str,Any]:
    print(f"Question: {question}\n")

    ans = qa({"query": question})

    print("\033[92m ---- Answer ---- \033[0m")
    print(ans["result"] + "\n")
        
    return ans
