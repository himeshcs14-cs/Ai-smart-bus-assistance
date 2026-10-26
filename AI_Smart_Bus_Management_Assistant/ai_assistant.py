import json, os
from dotenv import load_dotenv
load_dotenv()
def configured():
    load_dotenv(); return bool(os.getenv('WATSONX_API_KEY') and os.getenv('WATSONX_PROJECT_ID'))
def ask_bus_assistant(question, bus_records):
    load_dotenv(); key=os.getenv('WATSONX_API_KEY'); project=os.getenv('WATSONX_PROJECT_ID')
    url=os.getenv('WATSONX_URL','https://eu-de.ml.cloud.ibm.com'); model_id=os.getenv('WATSONX_MODEL_ID','ibm/granite-4-h-small')
    if not key or not project: raise RuntimeError('Add WATSONX_API_KEY and WATSONX_PROJECT_ID to your local .env file.')
    from ibm_watsonx_ai.foundation_models import ModelInference
    model=ModelInference(model_id=model_id,credentials={'apikey':key,'url':url},project_id=project)
    context=json.dumps(bus_records[:100],ensure_ascii=False,default=str)
    messages=[{'role':'system','content':'You are FleetIQ, a college bus management assistant. Use only the supplied records for current operational facts. If data is missing, say so. Do not invent buses, routes, numbers, or GPS locations. Distinguish facts from suggestions.'},{'role':'user','content':f'Bus records (JSON):\n{context}\n\nQuestion: {question}'}]
    response=model.chat(messages=messages)
    try:return response['choices'][0]['message']['content']
    except (KeyError,IndexError,TypeError):return str(response)
