from modal import Image, Stub, wsgi_app
import modal

stub = Stub(
    "example-web-flask",
    image=Image.debian_slim().pip_install("flask", "pymongo", "openai", "flask-cors"),
    secrets=[modal.Secret.from_name("flask_secrets")]
)

@stub.function()
def generate_vector(text):
    import pymongo
    import openai
    import os
    import json
    import random
    import time
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    while True:
        try:
            response = client.embeddings.create(
                input=text, model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except openai.RateLimitError:
            attempt += 1
            wait_time = min(2**attempt + random.random(), 60)
            if attempt == 10:
                break
            time.sleep(wait_time)
        except Exception as e:
            break
    return None

@stub.function()
def search_documents(query, collection_name):
    import pymongo
    import openai
    import os
    import json
    import random
    client = pymongo.MongoClient(
        f"mongodb+srv://vsuortiz1:{os.environ['MONGO_PASS']}@cluster0.woeb2iy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )

    db = client["Patient_Information"]
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    query_vector = generate_vector.local(query)
    collection = db[collection_name]
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index_" + collection_name,
                "path": "vector",
                "queryVector": query_vector,
                "numCandidates": 5,
                "limit": 1,
            }
        }
    ]
    results = collection.aggregate(pipeline)
    results = list(results)
    # print(results)
    user_message_with_context = "\n# User query:\n" + query
    if len(results) > 0:
        result = results[0]["summary"]

        user_message_with_context += (
            "# Context for the user query below, do not mention the query in your response:\n"
            + result
            + user_message_with_context
        )
        # print(user_message_with_context)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an expert physician that is answering questions for the patient.\n"
                + "If the user asks for information that is not consistent with the context explain potential misunderstandings"
                + "Talk to the patient in second person. Say you as if you were talking to the user.",
            },
            {
                "role": "user",
                "content": query,
            },
            {
                "role": "user",
                "content": user_message_with_context
            },
        ]
    )

    return {
        "response": response.choices[0].message.content
    }

@stub.function()
def mongo_updater(steps, heart, collection_name):
    import pymongo
    import os
    client = pymongo.MongoClient(
        f"mongodb+srv://vsuortiz1:{os.environ['MONGO_PASS']}@cluster0.woeb2iy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )

    db = client["Patient_Healthkit"]
    collection = db[collection_name]
    collection.drop()
    document = {
        'steps': steps,
        'heartbeat': heart
    }
    collection.insert_one(document)

    return { 
        "Modules" : 15, 
        "Subject" : "Data Structures and Algorithms", 
    }

@stub.function()
def convert_csv(query, collection_name):
    import pymongo
    import openai
    import os
    import json
    import random
    client = pymongo.MongoClient(
        f"mongodb+srv://vsuortiz1:{os.environ['MONGO_PASS']}@cluster0.woeb2iy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )

    db = client["Patient_Information"]
    collection = db[collection_name]
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    responses = []
    for item in collection.find():
        result = item["summary"]
        user_message_with_context = (
            "Convert this to JSON:\n"
            + result
            + f"Here is what I want in the Json Format {query}"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are creating JSONs based on sentences.\n"
                    + "Do not say anything except for the JSON",
                },
                {
                    "role": "user",
                    "content": user_message_with_context
                },
            ]
        )
        collection.update_one(
            { "_id": item["_id"] },
            { "$set": { "csv_data": json.loads(response.choices[0].message.content) } }
        )
    return responses

@stub.function()
@wsgi_app()
def flask_app():   
    from flask import Flask, request
    from flask_cors import CORS, cross_origin

    web_app = Flask(__name__)
    cors = CORS(web_app)
    @web_app.post("/search")
    @cross_origin()
    def search():
        return search_documents.remote(request.json["query"], request.json["collection_name"])

    @web_app.post("/convert_csv")
    @cross_origin()
    def foo():
        return convert_csv.remote(request.json["query"], request.json["collection_name"])

    @web_app.post("/mongo_updater")
    @cross_origin()
    def bruh():
        return mongo_updater.remote(request.json["steps"], request.json["heart"], request.json["collection_name"])

    return web_app

# curl -X POST -H "Content-Type: application/json" -d '{"query": "do I have hypertension", "collection_name": "o7s583"}' https://tanzhasan--example-web-flask-flask-app.modal.run/search_documents