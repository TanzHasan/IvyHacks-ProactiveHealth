import {
  Db,
  Collection,
  Document,
  WithoutId,
  OptionalUnlessRequiredId,
  Filter,
  UpdateFilter,
} from "mongodb";
import clientPromise from "./mongodb";

export interface Patient {
  patient_id: string;
  summary: string;
  csv_data: Record<string, any>;
  vector: number[];
}

export interface DoctorPatient {
  email: string;
  name: string;
  isDoctor: boolean;
  doctor: string;
  patient_id: string;
  patients: string[];
}

export interface Request {
  request_id: string;
  doctor_email: string;
  doctor_name: string;
  patient_id: string;
}

export interface HealthKitRecord {
  patient_id: string;
  start: string;
  end: string;
  unit: string;
  value: number;
}

export function generateId(): string {
  const characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let patientId = "";
  for (let i = 0; i < 8; i++) {
    patientId += characters.charAt(
      Math.floor(Math.random() * characters.length)
    );
  }
  return patientId;
}

export async function runQuery<T extends Document>(
  dbName: string,
  collectionName: string,
  query: object
): Promise<WithoutId<T>[]> {
  const client = await clientPromise;
  const db: Db = client.db(dbName);
  const collection: Collection<T> = db.collection(collectionName);

  const result: WithoutId<T>[] = await collection.find(query).toArray();
  return result;
}

async function insertQuery<T extends Document>(
  dbName: string,
  collectionName: string,
  document: OptionalUnlessRequiredId<T>
): Promise<void> {
  const client = await clientPromise;
  const db: Db = client.db(dbName);
  const collection: Collection<T> = db.collection(collectionName);

  await collection.insertOne(document);
}

async function updateQuery<T extends Document>(
  dbName: string,
  collectionName: string,
  filter: Filter<T>,
  update: UpdateFilter<T>
): Promise<void> {
  const client = await clientPromise;
  const db: Db = client.db(dbName);
  const collection: Collection<T> = db.collection(collectionName);

  await collection.updateMany(filter, update);
}

async function deleteQuery<T extends Document>(
  dbName: string,
  collectionName: string,
  filter: Filter<T>
): Promise<void> {
  const client = await clientPromise;
  const db: Db = client.db(dbName);
  const collection: Collection<T> = db.collection(collectionName);

  await collection.deleteMany(filter);
}

export async function createOrGetDoctorPatient(
  email: string,
  name: string
): Promise<DoctorPatient> {
  const existingEntries = await runQuery<DoctorPatient>(
    "Relationships",
    "doctor_patient",
    { email }
  );

  if (existingEntries.length > 0) {
    return existingEntries[0];
  } else {
    const newEntry: DoctorPatient = {
      email,
      name,
      isDoctor: false,
      doctor: "",
      patient_id: generateId(),
      patients: [],
    };

    await insertQuery<DoctorPatient>(
      "Relationships",
      "doctor_patient",
      newEntry
    );

    return newEntry;
  }
}

export async function addPatientRequest(
  doctorEmail: string,
  doctorName: string,
  patientId: string
): Promise<void> {
  const newRequest: OptionalUnlessRequiredId<Request> = {
    request_id: generateId(),
    doctor_email: doctorEmail,
    doctor_name: doctorName,
    patient_id: patientId,
  };

  await insertQuery<Request>("Relationships", "switch_requests", newRequest);
}

export async function handlePatientRequest(
  patientId: string,
  doctorEmail: string,
  accept: boolean
): Promise<void> {
  const patient = await runQuery<DoctorPatient>(
    "Relationships",
    "doctor_patient",
    {
      patient_id: patientId,
    }
  );

  console.log(patient);

  if (patient.length > 0) {
    const currentDoctor = patient[0].doctor;

    if (accept) {
      await updateQuery<DoctorPatient>(
        "Relationships",
        "doctor_patient",
        { email: currentDoctor },
        { $pull: { patients: patientId } }
      );

      await updateQuery<DoctorPatient>(
        "Relationships",
        "doctor_patient",
        { email: doctorEmail },
        { $addToSet: { patients: patientId } }
      );

      await updateQuery<DoctorPatient>(
        "Relationships",
        "doctor_patient",
        { patient_id: patientId },
        { $set: { doctor: doctorEmail } }
      );
    }

    await deleteQuery<Request>("Relationships", "switch_requests", {
      patient_id: patientId,
    });
  }
}
