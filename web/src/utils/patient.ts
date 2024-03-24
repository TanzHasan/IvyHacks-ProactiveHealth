import { Patient } from "@/utils/mongoquery";

export function patientsToTable(patients: Patient[]): Record<string, any[]> {
  const patientCsvs = patients.map((patient) => patient.csv_data);
  return patientCsvs.reduce((acc, curr) => {
    const keys = Object.keys(curr);
    for (const key of keys) {
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(curr[key]);
    }
    return acc;
  }, {});
}
