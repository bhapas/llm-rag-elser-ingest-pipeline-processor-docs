# import modules
import json
import boto3
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.embeddings.bedrock import BedrockEmbeddings
from langchain.globals import set_debug, set_verbose
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_elasticsearch import ElasticsearchStore
from langchain.llms.bedrock import Bedrock
from elasticsearch import Elasticsearch
import requests
from search import Search

set_debug(True)
set_verbose(True)
es = Search()

bedrock_client = boto3.client(
    service_name="bedrock-runtime", region_name="us-east-1")
embeddings = BedrockEmbeddings(client=bedrock_client)


vector_store = ElasticsearchStore(
    es_connection=Elasticsearch(hosts="http://localhost:9200",connections_per_node=5),
    index_name="my_documents",
    embedding=embeddings,
    strategy=ElasticsearchStore.SparseVectorRetrievalStrategy(),
)

documents = es.reindex()

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

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=512, chunk_overlap=256
)
docs = text_splitter.create_documents(content, metadatas=metadata)

vector_store.from_documents(
    documents=docs,
    es_connection=Elasticsearch(hosts="http://localhost:9200",connections_per_node=5),
    index_name="my_documents",
    strategy=ElasticsearchStore.SparseVectorRetrievalStrategy(),
)



default_model_id = "anthropic.claude-v2:1"
AWS_MODEL_ID = input(f"AWS model [default: {default_model_id}]: ") or default_model_id
llm = Bedrock(client=bedrock_client, model_id=AWS_MODEL_ID)

retriever = vector_store.as_retriever()

qa = RetrievalQA.from_llm(llm=llm, retriever=retriever,
                          return_source_documents=True)

questions = [
    "How do I use 'append' ingest pipeline processor?",
]
question = questions[0]
print(f"Question: {question}\n")

ans = qa({"query": question})

print("\033[92m ---- Answer ---- \033[0m")
print(ans["result"] + "\n")
print("\033[94m ---- Sources ---- \033[0m")
for doc in ans["source_documents"]:
    print("Name: " + doc.metadata["name"])
    print("Content: " + doc.page_content)
    print("-------\n")
