import { SignIn, SignOut } from "@/components/auth-buttons";
import { authOptions } from "@/utils/auth";
import { getServerSession } from "next-auth";
import {
  runQuery,
  Patient,
  createOrGetDoctorPatient,
  HealthKitRecord,
  Request,
} from "@/utils/mongoquery";
import { patientsToTable } from "@/utils/patient";
import { PatientTable } from "@/components/patient-table";
import { HeartRateChart } from "@/components/patient-chart";
import { SwitchRequest } from "@/components/switch-request";

export default async function Home() {
  const session = await getServerSession(authOptions);

  if (session?.user == undefined) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-between p-24">
        <h1>Proactive Health</h1>
        <div>{}</div>
        <SignIn />
        <SignOut />
      </main>
    );
  }

  const doctorPatientEntry = await createOrGetDoctorPatient(
    session.user.email!,
    session.user.name!
  );

  const patientIdToFind = "o7s583"; // TODO: change this to doctor patient entry id
  const patientsPromise = runQuery<Patient>(
    "Patient_Information",
    patientIdToFind,
    { patient_id: patientIdToFind }
  );

  const hkDataPromise = runQuery<HealthKitRecord>(
    "GPTFUN",
    "HKQuantityTypeIdentifierHeartRate",
    { patient_id: patientIdToFind }
  ).then((hkData) =>
    hkData.sort(
      (a, b) => new Date(a.start).getTime() - new Date(b.start).getTime()
    )
  );

  const requestsPromise = runQuery<Request>(
    "Relationships",
    "switch_requests",
    { patient_id: patientIdToFind }
  );

  const [patients, hkData, requests] = await Promise.all([
    patientsPromise,
    hkDataPromise,
    requestsPromise,
  ]);

  const table = patientsToTable(patients);

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1>Proactive Health</h1>
      <PatientTable table={table} />
      <HeartRateChart hkHeartRateData={hkData} width={500} height={300} />
      <div>Your patient id {doctorPatientEntry.patient_id}</div>
      <SignIn />
      <SignOut />
      {requests.length > 0 && (
        <div>
          <h2 className="font-bold">Switch Requests</h2>
          <div>
            {requests.map((request) => (
              <SwitchRequest key={request.request_id} request={request} />
            ))}
          </div>
        </div>
      )}
    </main>
  );
}
