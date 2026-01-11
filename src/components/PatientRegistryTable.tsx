import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Search, Filter, Download, Plus, Eye, ChevronUp, ChevronDown, Loader2 } from "lucide-react";
import { usePatients } from "../hooks/usePatients";
import type { Patient } from "../api/types";
import { downloadCohortCsv } from "../api/cohort";

interface PatientRegistryTableProps {
  onPatientSelect: (mrn: string) => void;
}

export function PatientRegistryTable({ onPatientSelect }: PatientRegistryTableProps) {
  const [selectedPatients, setSelectedPatients] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [filterGender, setFilterGender] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState<string>("dna_id");
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>("asc");

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const { data: patientsData, isLoading, error, refetch } = usePatients({
    page,
    limit: 50,
    search: debouncedSearch || undefined,
    gender: filterGender !== "all" ? filterGender : undefined,
    sortBy: sortField,
    sortOrder: sortDirection,
  });

  const patients = patientsData || [];

  const handleExport = () => {
    const selectedData = patients
      .filter(p => selectedPatients.includes(p.dna_id))
      .map(p => ({
        dna_id: p.dna_id,
        age: p.age,
        gender: p.gender,
        nationality: p.nationality,
        enrollment_date: p.enrollment_date,
        systolic_bp: p.systolic_bp,
        diastolic_bp: p.diastolic_bp,
        heart_rate: p.heart_rate,
        bmi: p.bmi,
        hba1c: p.hba1c,
        echo_ef: p.echo_ef,
        mri_ef: p.mri_ef,
        data_completeness: p.data_completeness,
      }));
    downloadCohortCsv(selectedData, 'patient_registry_export.csv');
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedPatients(patients.map(p => p.dna_id));
    } else {
      setSelectedPatients([]);
    }
  };

  const handleSelectPatient = (dnaId: string, checked: boolean) => {
    if (checked) {
      setSelectedPatients(prev => [...prev, dnaId]);
    } else {
      setSelectedPatients(prev => prev.filter(id => id !== dnaId));
    }
  };

  const SortableHeader = ({ field, children }: { field: string; children: React.ReactNode }) => (
    <TableHead 
      className="cursor-pointer hover:bg-muted/50" 
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center space-x-1">
        <span>{children}</span>
        {sortField === field && (
          sortDirection === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
        )}
      </div>
    </TableHead>
  );

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-500">
            <p>Error loading patients: {error}</p>
            <Button onClick={() => refetch()} className="mt-4">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Patient Registry</CardTitle>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">
                {patients.length} patients
              </Badge>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Patient
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters and Search */}
          <div className="flex items-center space-x-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by DNA ID, nationality, city..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select value={filterGender} onValueChange={(value) => { setFilterGender(value); setPage(1); }}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Gender" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Genders</SelectItem>
                <SelectItem value="Male">Male</SelectItem>
                <SelectItem value="Female">Female</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </Button>

            <Button 
              variant="outline" 
              size="sm" 
              disabled={selectedPatients.length === 0}
              onClick={handleExport}
            >
              <Download className="h-4 w-4 mr-2" />
              Export ({selectedPatients.length})
            </Button>
          </div>

          {/* Patient Table */}
          <div className="border rounded-lg overflow-hidden">
            {isLoading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading patients...</span>
              </div>
            ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedPatients.length === patients.length && patients.length > 0}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <SortableHeader field="dna_id">DNA ID</SortableHeader>
                  <SortableHeader field="age">Age</SortableHeader>
                  <SortableHeader field="gender">Gender</SortableHeader>
                  <TableHead>Nationality</TableHead>
                  <SortableHeader field="enrollment_date">Enrollment Date</SortableHeader>
                  <TableHead>BP (mmHg)</TableHead>
                  <TableHead>BMI</TableHead>
                  <TableHead>Echo EF</TableHead>
                  <TableHead>MRI EF</TableHead>
                  <SortableHeader field="data_completeness">Data Completeness</SortableHeader>
                  <TableHead>Imaging</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={13} className="text-center py-8 text-muted-foreground">
                      No patients found
                    </TableCell>
                  </TableRow>
                ) : (
                  patients.map((patient) => (
                    <TableRow key={patient.dna_id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedPatients.includes(patient.dna_id)}
                          onCheckedChange={(checked) => handleSelectPatient(patient.dna_id, checked as boolean)}
                        />
                      </TableCell>
                      <TableCell className="font-mono">
                        <button
                          onClick={() => onPatientSelect(patient.dna_id)}
                          className="text-[#00a2ddff] hover:underline cursor-pointer"
                        >
                          {patient.dna_id}
                        </button>
                      </TableCell>
                      <TableCell>{patient.age ?? '-'}</TableCell>
                      <TableCell>{patient.gender ?? '-'}</TableCell>
                      <TableCell>{patient.nationality ?? '-'}</TableCell>
                      <TableCell>{patient.enrollment_date ? new Date(patient.enrollment_date).toLocaleDateString() : '-'}</TableCell>
                      <TableCell>
                        {patient.systolic_bp && patient.diastolic_bp 
                          ? `${Math.round(Number(patient.systolic_bp))}/${Math.round(Number(patient.diastolic_bp))}`
                          : '-'
                        }
                      </TableCell>
                      <TableCell>
                        {patient.bmi ? Number(patient.bmi).toFixed(1) : '-'}
                      </TableCell>
                      <TableCell>
                        {patient.echo_ef ? `${patient.echo_ef}%` : '-'}
                      </TableCell>
                      <TableCell>
                        {patient.mri_ef ? `${patient.mri_ef}%` : '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <div className="w-12 bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                patient.data_completeness >= 80 ? 'bg-green-500' :
                                patient.data_completeness >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${patient.data_completeness}%` }}
                            />
                          </div>
                          <span className="text-xs">{patient.data_completeness}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-1">
                          {patient.has_echo && <Badge variant="secondary" className="text-xs">Echo</Badge>}
                          {patient.has_mri && <Badge variant="secondary" className="text-xs">MRI</Badge>}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => onPatientSelect(patient.dna_id)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            )}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              Page {page}
            </div>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || isLoading}
              >
                Previous
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setPage(p => p + 1)}
                disabled={patients.length < 50 || isLoading}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}