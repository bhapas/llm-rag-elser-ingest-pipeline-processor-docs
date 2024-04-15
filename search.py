import json
from pprint import pprint
import os
import time
import requests
import urllib3
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()


class Search:
    
    def __init__(self):
        self.es = Elasticsearch(hosts="http://localhost:9200",connections_per_node=15)  # <-- connection options need to be added here
        client_info = self.es.info()
        print('Connected to Elasticsearch!')
        pprint(client_info.body)


    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        print('Deleted index my_documents')
        self.es.indices.create(
            index='my_documents',
            mappings={
                'properties': {
                    'elser_embedding': {
                        'type': 'sparse_vector',
                    },
                    "page_content": { 
                        "type": "text" 
                    }
                }
            },
            settings={
                'index': {
                    'default_pipeline': 'elser-ingest-pipeline'
                }
            }
        )
        print('Created index my_documents')
        
    def delete_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)

    
    def insert_document(self, document):
        return self.es.index(index='my_documents', body=document)
    
    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append(document)
        self.es.bulk(operations=operations, timeout='420s')
        return documents

    def reindex(self):
        self.create_index()
    
    def search(self, **query_args):
        return self.es.search(index='my_documents', **query_args)
    
    def retrieve_document(self, id):
        return self.es.get(index='my_documents', id=id)
    
    def deploy_elser(self):
        # download ELSER v2
        self.es.ml.put_trained_model(model_id='.elser_model_1',
                                     input={'field_names': ['text_field']})
        
        # wait until ready
        while True:
            status = self.es.ml.get_trained_models(model_id='.elser_model_1',
                                                   include='definition_status')
            if status['trained_model_configs'][0]['fully_defined']:
                # model is ready
                break
            time.sleep(1)

        # deploy the model
        self.es.ml.start_trained_model_deployment(model_id='.elser_model_1')

        # define a pipeline
        # self.es.ingest.put_pipeline(
        #     id='elser-ingest-pipeline',
        #     processors=[
        #         {
        #             'inference': {
        #                 'model_id': '.elser_model_1',
        #                 'input_output': [
        #                     {
        #                         'input_field': 'page_content',
        #                         'output_field': 'elser_embedding',
        #                     }
        #                 ]
        #             }
        #         }
        #     ]
        # )
        
    def delete_elser(self):
        self.es.ml.delete_trained_model(model_id='.elser_model_1', force=True)