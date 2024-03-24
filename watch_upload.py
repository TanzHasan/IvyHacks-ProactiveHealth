from health import HealthData
import pymongo
import os
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

client = pymongo.MongoClient(
    f"mongodb+srv://vsuortiz1:{os.environ['MONGO_PASS']}@cluster0.woeb2iy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
# client = pymongo.MongoClient('mongodb://localhost:27017/')

if __name__ == "__main__":
    patient_id = "o7s583"
    db = client["GPTFUN"]

    FILE = "./apple_health_export/export.xml"
    data = HealthData.read(
        FILE,
        include_me=True,
        include_activity_summaries=True,
        include_correlations=True,
        include_records=True,
        include_workouts=True,
    )

    print(data.me.biological_sex)
    print(f"{len(data.activity_summaries)} activity records")
    print(f"{len(data.correlations)} correlations")
    print(f"{len(data.records)} records")
    print(f"{len(data.workouts)} workouts")

    a = defaultdict(int)
    for i in range(350000):
        record = data.records[-i-1]
        if 'HKQ' in record.name and a[record.name] < 100:
            a[record.name] += 1
            document = {
                "patient_id": patient_id,
                "start": record.start,
                "end": record.end,
                "unit": record.unit,
                "value": record.value
            }
            db[record.name].insert_one(document)
