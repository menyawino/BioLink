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
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        {getIcon()}
        <h3 className="mt-4 text-lg font-medium text-muted-foreground">{title}</h3>
        <p className="mt-2 text-sm text-muted-foreground max-w-md">
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
