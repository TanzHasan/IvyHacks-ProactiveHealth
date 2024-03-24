import pymongo
import openai
import os
import json
from dotenv import load_dotenv
from basic import generate_vector

load_dotenv()

client = pymongo.MongoClient(
    f"mongodb+srv://vsuortiz1:{os.environ['MONGO_PASS']}@cluster0.woeb2iy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

db = client["Patient_Information"]
collection = db["o7s583"]

client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def search_documents(query, collection_name):
    client = pymongo.MongoClient(
        f"mongodb+srv://vsuortiz1:{os.environ['MONGO_PASS']}@cluster0.woeb2iy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )

    db = client["Patient_Information"]
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    query_vector = generate_vector(query)
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
    print(results)
    user_message_with_context = "\n# User query:\n" + query
    if len(results) > 0:
        result = results[0]["summary"]

        user_message_with_context += (
            "# Context for the user query below, do not mention the query in your response:\n"
            + result
            + user_message_with_context
        )
        print(user_message_with_context)

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

    return response.choices[0].message.content


def convert_csv(query):
    # results = db.patient.aggregate(pipeline)
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

# print(search_documents("do i have hypertension", "o7s583"))
