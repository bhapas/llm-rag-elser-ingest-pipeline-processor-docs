import re
import requests
import urllib3
from llm_testing import run_llm_test

from flask import Flask, render_template, request
from search import Search

app = Flask(__name__)
es = Search()

@app.get('/')
def index():
    return render_template('index.html')


@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    from_ = request.form.get('from_', type=int, default=0)
    results = run_llm_test(es.qa,query)
    # results = es.search(
    #    query={
    #         'multi_match': {
    #             'query': query,
    #             'fields': ['name', 'path', 'download_url','content'],
    #         }
    #     }, size=10, from_=from_
    # )
    return render_template('index.html', results=(results['result']+ "\n"),
                           query=query, from_=from_, total=1)



@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document['_source']['name']
    url = document['_source']['download_url'].split('\n')
    response = requests.get(url[0]) 

    return render_template('document.html', title=title, paragraphs=response)


@app.cli.command()
def deploy_elser():
    """Deploy the ELSER v2 model to Elasticsearch."""
    try:
        es.deploy_elser()
    except Exception as exc:
        print(f'Error: {exc}')
    else:
        print(f'ELSER model deployed.')

@app.cli.command()
def delete_elser():
    """Delere the ELSER v2 model to Elasticsearch."""
    try:
        es.delete_elser()
    except Exception as exc:
        print(f'Error: {exc}')
    else:
        print(f'ELSER model deleted.')