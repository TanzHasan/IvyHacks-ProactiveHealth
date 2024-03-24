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


def search_documents(query):
    query_vector = generate_vector(query)
    k = 1
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "vector",
                "queryVector": query_vector,
                "numCandidates": 5,
                "limit": 1,
            }
        }
    ]
    results = db.patient.aggregate(pipeline)
    results = list(results)
    user_message_with_context = "\n# User query:\n" + query
    if len(results) > 0:
        
        result = "Patient 109 was admitted to the hospital on November 4, 2137, at 19:36 due to a hypertensive emergency. The admission type was emergency, and the patient was admitted from the emergency room. The patient was discharged on November 21, 2137, at 18:13, and went back home. The patient's insurance was government-based, and they spoke English. The patient's religion, marital status, and ethnicity were not specified. The patient was not deceased during this hospital stay, and had chart events data available."
        user_message_with_context += (
            "# Context for the user query below, do not mention the query in your response:\n"
            + result
            + user_message_with_context
        )

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

# convert_csv("{ethnicity: only one of {Black, White, Asian-American, Hispanic, N/A}, dead: 0 if alive else 1, marital_status: string}")
