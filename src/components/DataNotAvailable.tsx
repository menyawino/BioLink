import React from "react";
import { Card, CardContent } from "./ui/card";
import { AlertCircle, Database, FileQuestion } from "lucide-react";

interface DataNotAvailableProps {
  title: string;
  message?: string;
  type?: 'not-in-database' | 'empty-for-patient' | 'feature-not-available';
}

export function DataNotAvailable({ title, message, type = 'not-in-database' }: DataNotAvailableProps) {
  const getIcon = () => {
    switch (type) {
      case 'not-in-database':
        return <Database className="h-8 w-8 text-muted-foreground" />;
      case 'empty-for-patient':
        return <FileQuestion className="h-8 w-8 text-muted-foreground" />;
      case 'feature-not-available':
        return <AlertCircle className="h-8 w-8 text-muted-foreground" />;
      default:
        return <AlertCircle className="h-8 w-8 text-muted-foreground" />;
    }
  };

  const getDefaultMessage = () => {
    switch (type) {
      case 'not-in-database':
        return 'This data type is not available in the EHVol database schema.';
      case 'empty-for-patient':
        return 'No data recorded for this patient.';
      case 'feature-not-available':
        return 'This feature is not yet available.';
      default:
        return 'Data not available.';
    }
  };

  return (
    <Card className="empty-state-card border-dashed">
      <CardContent className="flex flex-col items-center justify-center px-6 py-12 text-center md:py-14">
        <span className="empty-state-icon">
          {getIcon()}
        </span>
        <p className="empty-state-kicker">
          {type === 'feature-not-available' ? 'Feature Status' : 'Patient Data'}
        </p>
        <h3 className="empty-state-title">{title}</h3>
        <p className="empty-state-text max-w-lg">
          {message || getDefaultMessage()}
        </p>
      </CardContent>
    </Card>
  );
}

// Small inline version for individual fields
export function FieldNotAvailable({ label }: { label?: string }) {
  return (
    <span className="text-muted-foreground text-sm italic">
      {label || 'Not recorded'}
    </span>
  );
}
