import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Pill, Clock, AlertTriangle, Plus } from "lucide-react";

interface MedicationsProps {
  medications: Array<{
    id: string;
    name: string;
    dosage: string;
    frequency: string;
    prescribedDate: string;
    indication: string;
    status: 'active' | 'discontinued' | 'temporary';
    nextDose?: string;
  }>;
}

export function Medications({ medications }: MedicationsProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'discontinued': return 'secondary';
      case 'temporary': return 'outline';
      default: return 'default';
    }
  };

  const activeMedications = medications.filter(med => med.status === 'active');
  const inactiveMedications = medications.filter(med => med.status !== 'active');

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3>Current Medications</h3>
        <Button size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add Medication
        </Button>
      </div>

      <div className="grid gap-4">
        {activeMedications.map((medication) => (
          <Card key={medication.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-blue-100 rounded-full">
                    <Pill className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="mb-1">{medication.name}</h4>
                    <p className="text-muted-foreground mb-2">{medication.dosage} • {medication.frequency}</p>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>For: {medication.indication}</span>
                      <span>Since: {medication.prescribedDate}</span>
                    </div>
                    {medication.nextDose && (
                      <div className="flex items-center space-x-1 mt-2 text-sm text-orange-600">
                        <Clock className="h-3 w-3" />
                        <span>Next dose: {medication.nextDose}</span>
                      </div>
                    )}
                  </div>
                </div>
                <Badge variant={getStatusVariant(medication.status)}>
                  {medication.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {inactiveMedications.length > 0 && (
        <div className="mt-8">
          <h4 className="mb-4 text-muted-foreground">Previous Medications</h4>
          <div className="space-y-2">
            {inactiveMedications.map((medication) => (
              <Card key={medication.id} className="opacity-60">
                <CardContent className="p-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="line-through">{medication.name}</span>
                      <span className="text-sm text-muted-foreground ml-2">
                        {medication.dosage}
                      </span>
                    </div>
                    <Badge variant={getStatusVariant(medication.status)}>
                      {medication.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      <Card className="border-orange-200 bg-orange-50">
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
            <div>
              <h4 className="text-orange-800">Medication Reminders</h4>
              <p className="text-sm text-orange-700 mt-1">
                Remember to take medications as prescribed. Lisinopril should be taken with food to reduce stomach upset.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}