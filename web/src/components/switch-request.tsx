import { Request, handlePatientRequest } from "@/utils/mongoquery";

export type SwitchRequestProps = {
  request: Request;
};

export function SwitchRequest({ request }: SwitchRequestProps) {
  return (
    <div>
      <p>{request.doctor_name} is requesting to be your doctor.</p>
      <form
        action={async () => {
          "use server";
          await handlePatientRequest(
            request.patient_id,
            request.doctor_email,
            true
          );
        }}
      >
        <button type="submit">Accept</button>
      </form>
      <form
        action={async () => {
          "use server";
          await handlePatientRequest(
            request.patient_id,
            request.doctor_email,
            false
          );
        }}
      >
        <button type="submit">Reject</button>
      </form>
    </div>
  );
}
