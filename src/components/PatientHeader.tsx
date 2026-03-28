import { Avatar, AvatarFallback } from "./ui/avatar";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";
import { CalendarDays, Phone, MapPin, Heart, Hash } from "lucide-react";

interface PatientHeaderProps {
  patient: {
    id: string;
    mrn: string;
    name: string;
    age: number;
    gender: string;
    dateOfBirth: string;
    phone: string;
    address: string;
    riskLevel: 'low' | 'moderate' | 'high';
    lastVisit: string;
  };
}

export function PatientHeader({ patient }: PatientHeaderProps) {
  const getRiskBadgeVariant = (level: string) => {
    switch (level) {
      case 'high': return 'destructive';
      case 'moderate': return 'default';
      case 'low': return 'secondary';
      default: return 'default';
    }
  };

  return (
    <Card className="patient-summary-card">
      <CardContent className="patient-summary-content p-6">
        <div className="patient-summary-grid grid gap-6 xl:grid-cols-[minmax(0,1fr)_16rem] xl:items-start">
          <div className="space-y-5">
            <div className="flex items-start gap-4">
              <Avatar className="h-16 w-16 border border-border/70 shadow-sm">
                <AvatarFallback className="bg-primary text-primary-foreground text-lg">
                  {patient.name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0 space-y-2">
                <div>
                  <p className="section-kicker">Patient Workspace</p>
                  <h1 className="text-[2rem] font-semibold tracking-[-0.04em] text-foreground">{patient.name}</h1>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  <div className="inline-flex items-center gap-1.5 rounded-full border border-border/70 bg-background/80 px-3 py-1.5">
                    <Hash className="h-3.5 w-3.5" />
                    <span className="font-mono text-[0.82rem] tracking-[0.08em] uppercase">{patient.mrn}</span>
                  </div>
                  <div className="inline-flex items-center gap-1.5 rounded-full border border-border/70 bg-background/80 px-3 py-1.5">
                    <span>{patient.age} years old</span>
                  </div>
                  <div className="inline-flex items-center gap-1.5 rounded-full border border-border/70 bg-background/80 px-3 py-1.5">
                    <span>{patient.gender}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <div className="patient-summary-meta-item">
                <CalendarDays className="h-4 w-4 text-primary" />
                <div>
                  <p className="patient-summary-label">Date of Birth</p>
                  <p className="patient-summary-value">{patient.dateOfBirth}</p>
                </div>
              </div>
              <div className="patient-summary-meta-item">
                <Phone className="h-4 w-4 text-primary" />
                <div>
                  <p className="patient-summary-label">Phone</p>
                  <p className="patient-summary-value">{patient.phone}</p>
                </div>
              </div>
              <div className="patient-summary-meta-item">
                <MapPin className="h-4 w-4 text-primary" />
                <div>
                  <p className="patient-summary-label">Location</p>
                  <p className="patient-summary-value">{patient.address}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="patient-risk-panel rounded-2xl border border-border/70 bg-background/80 p-5 xl:text-right">
            <div className="flex items-center gap-2 xl:justify-end">
              <Heart className="h-4 w-4 text-red-500" />
              <span className="text-sm font-medium text-foreground">Cardiovascular Risk</span>
            </div>
            <Badge variant={getRiskBadgeVariant(patient.riskLevel)} className="mt-3">
              {patient.riskLevel.toUpperCase()} RISK
            </Badge>
            <p className="mt-4 text-sm text-muted-foreground">Last visit: {patient.lastVisit}</p>
            <div className="mt-4 rounded-xl border border-border/70 bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
              Profile summary reflects the most complete registry record available for this patient.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}