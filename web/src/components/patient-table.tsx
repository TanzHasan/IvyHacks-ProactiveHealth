import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export type PatientTableProps = {
  table: Record<string, any[]>;
};

export function PatientTable({ table }: PatientTableProps) {
  const numRows = Object.keys(table).reduce((acc, curr) => {
    return Math.max(acc, table[curr].length);
  }, 0);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {Object.keys(table).map((key) => (
            <TableHead key={key}>{key}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: numRows }).map((_, i) => (
          <TableRow key={i}>
            {Object.keys(table).map((key) => (
              <TableCell key={key}>{table[key][i]}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
