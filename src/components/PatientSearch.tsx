import { useState, useEffect } from "react";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { Search, X, Loader2 } from "lucide-react";
import { Badge } from "./ui/badge";
import { usePatientSearch } from "../hooks/usePatients";

interface PatientSearchProps {
  currentMrn: string;
  onPatientSelect: (dnaId: string) => void;
}

export function PatientSearch({ currentMrn, onPatientSelect }: PatientSearchProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [showResults, setShowResults] = useState(false);

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Use API hook for searching
  const { data: searchResults, isLoading } = usePatientSearch(debouncedSearch, 10);

  useEffect(() => {
    if (searchTerm.trim().length > 0) {
      setShowResults(true);
    } else {
      setShowResults(false);
    }
  }, [searchTerm]);

  const handleSelectPatient = (dnaId: string) => {
    onPatientSelect(dnaId);
    setSearchTerm("");
    setShowResults(false);
  };

  const handleClear = () => {
    setSearchTerm("");
    setShowResults(false);
  };

  return (
    <div className="relative">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by DNA ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-8"
              />
              {searchTerm && (
                <button
                  onClick={handleClear}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            {currentMrn && (
              <Badge variant="outline" className="whitespace-nowrap">
                Current: {currentMrn}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Search Results Dropdown */}
      {showResults && (
        <Card className="absolute top-full mt-2 w-full z-50 shadow-lg">
          <CardContent className="p-2">
            {isLoading ? (
              <div className="flex items-center justify-center p-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Searching...</span>
              </div>
            ) : searchResults && searchResults.length > 0 ? (
              <div className="space-y-1 max-h-80 overflow-y-auto">
                {searchResults.map((patient) => (
                  <button
                    key={patient.dna_id}
                    onClick={() => handleSelectPatient(patient.dna_id)}
                    className="w-full text-left p-3 hover:bg-muted rounded-md transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-sm text-[#00a2ddff]">
                            {patient.dna_id}
                          </span>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {Number(patient.age) || 'N/A'} years • {patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : patient.gender || 'Unknown'} • {patient.nationality || 'Unknown nationality'}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Data completeness: {Number(patient.data_completeness)}%
                        </div>
                      </div>
                      {patient.dna_id === currentMrn && (
                        <Badge variant="secondary" className="text-xs">
                          Current
                        </Badge>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : debouncedSearch.length > 0 ? (
              <p className="text-muted-foreground text-center p-4">
                No patients found matching "{debouncedSearch}"
              </p>
            ) : (
              <p className="text-muted-foreground text-center p-4">
                Start typing to search patients...
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
