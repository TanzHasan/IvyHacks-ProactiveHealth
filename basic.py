import csv
import pymongo
import time
import random
import openai
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

client = pymongo.MongoClient(
    f"mongodb+srv://vsuortiz1:{os.environ['MONGO_PASS']}@cluster0.woeb2iy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
# client = pymongo.MongoClient('mongodb://localhost:27017/')

db = client["Patient_Information"]


client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

subject_id_to_patient = {}

def int_to_unique_str(integer, length=8):
    """
    Converts an integer to a unique string of specified length.
    This implementation uses base-36 encoding to ensure uniqueness.
    """
    # Base-36 encoding uses 0-9 and then a-z for 10-35
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    # if integer < 0:
    #     sign = "-"
    #     integer = -integer
    # else:
    #     sign = ""
    
    # Convert to base-36
    encoded = ''
    while integer > 0:
        integer, remainder = divmod(integer, 36)
        encoded = chars[remainder] + encoded
    
    # Ensure the string is of the desired length
    encoded = encoded.rjust(length, '0')
    
    return encoded[:length]

def process_csv(file_path):
    rows = []
    with open(file_path, "r") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            rows.append(row)
        for i in range(0, 130):
            row = rows[i]
            # if row["subject_id"] not in subject_id_to_patient:
            #     subject_id_to_patient[row["subject_id"]] = secrets.token_hex(4)
            if row["subject_id"] == "109":
                subject_id_to_patient[row["subject_id"]] = "o7s583"
            else:
                continue
            patient_id = subject_id_to_patient[row["subject_id"]]
            collection = db[patient_id]
            summaries = generate_summary_per_row(row)
            vector = generate_vector(summaries)
            document = {
                "patient_id": patient_id,
                "csv_data": row,
                "summary": summaries,
                "vector": vector,
            }

            collection.insert_one(document)


def generate_summary_per_row(row):

    prompt = "Generate a summary of the patient's hospital stays based on the following information:\n\n"
    prompt += f"{row}"
    print(prompt)
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-3.5-turbo",
    )
    print(response.choices[0].message.content)
    summary = response.choices[0].message.content

    return summary


def generate_vector(text):
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


def format_date(datetime_str):
    return datetime_str.split("T")[0]


if __name__ == "__main__":
    csv_file_path = "./admissions_additional.csv"
    process_csv(csv_file_path)