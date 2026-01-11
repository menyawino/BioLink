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
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="bg-primary text-primary-foreground">
                {patient.name.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="mb-1">{patient.name}</h1>
              <div className="flex items-center space-x-4 text-muted-foreground mb-1">
                <div className="flex items-center space-x-1">
                  <Hash className="h-4 w-4" />
                  <span className="font-mono">{patient.mrn}</span>
                </div>
              </div>
              <div className="flex items-center space-x-4 text-muted-foreground">
                <span>{patient.age} years old • {patient.gender}</span>
                <div className="flex items-center space-x-1">
                  <CalendarDays className="h-4 w-4" />
                  <span>{patient.dateOfBirth}</span>
                </div>
              </div>
              <div className="flex items-center space-x-4 mt-2 text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <Phone className="h-4 w-4" />
                  <span>{patient.phone}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <MapPin className="h-4 w-4" />
                  <span>{patient.address}</span>
                </div>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-2 mb-2">
              <Heart className="h-4 w-4 text-red-500" />
              <span className="text-sm">Cardiovascular Risk</span>
            </div>
            <Badge variant={getRiskBadgeVariant(patient.riskLevel)}>
              {patient.riskLevel.toUpperCase()} RISK
            </Badge>
            <p className="text-sm text-muted-foreground mt-2">
              Last visit: {patient.lastVisit}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}