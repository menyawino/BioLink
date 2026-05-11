import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Search, Download, Eye, ChevronUp, ChevronDown, Loader2 } from "lucide-react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { usePatients } from "../hooks/usePatients";
import type { DatasetFilter } from "../api/patients";
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
  const [dataset, setDataset] = useState<DatasetFilter>("all");
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
    dataset,
    sortBy: sortField,
    sortOrder: sortDirection,
  });

  const patients = patientsData || [];
  const activeFilters = [filterGender !== "all", dataset !== "all", Boolean(debouncedSearch)].filter(Boolean).length;

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

  const tableContainerRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: patients.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: useCallback(() => 52, []),
    overscan: 5,
  });

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
    <div className="registry-shell space-y-5">
      <div className="registry-hero flex flex-wrap items-end justify-between gap-4 xl:flex-nowrap xl:items-start">
        <div className="space-y-2 xl:max-w-3xl">
          <span className="section-kicker">Registry Workspace</span>
          <div>
            <h2 className="section-title">Patient Registry</h2>
            <p className="section-subtitle max-w-3xl">
              Review the live registry, refine the cohort, and move into patient detail with a faster, cleaner table workflow.
            </p>
          </div>
        </div>

        <div className="registry-meta-grid grid w-full gap-3 sm:grid-cols-3 xl:w-[33rem] xl:flex-shrink-0">
          <div className="metric-tile">
            <span className="metric-label">Visible on page</span>
            <strong className="metric-value">{patients.length}</strong>
          </div>
          <div className={`metric-tile ${selectedPatients.length > 0 ? 'border-[#00a2dd]/30 bg-[#00a2dd]/5' : ''}`}>
            <span className="metric-label">Selected</span>
            <strong className={`metric-value ${selectedPatients.length > 0 ? 'text-[#00a2dd]' : ''}`}>{selectedPatients.length}</strong>
          </div>
          <div className={`metric-tile ${activeFilters > 0 ? 'border-amber-300 bg-amber-50/60' : ''}`}>
            <span className="metric-label">Active filters</span>
            <strong className={`metric-value ${activeFilters > 0 ? 'text-amber-600' : ''}`}>{activeFilters}</strong>
          </div>
        </div>
      </div>

      <Card className="registry-card">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="text-lg font-semibold tracking-tight">Patient Registry</CardTitle>
              <p className="text-sm text-muted-foreground">Sorted by {sortField.replace(/_/g, ' ')} in {sortDirection} order.</p>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="registry-badge">
                {patients.length} patients
              </Badge>
              <Badge variant="secondary" className="px-3 py-1 text-xs font-medium">
                Read-only live registry
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Filters and Search */}
          <div className="registry-toolbar flex flex-wrap items-center gap-3 xl:flex-nowrap xl:items-center">
            <div className="registry-search-group flex-1 min-w-[18rem] xl:min-w-[22rem]">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by patient ID, city, nationality, or cohort clue..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="registry-search-input pl-10"
                />
              </div>
            </div>
            
            <Select value={filterGender} onValueChange={(value) => { setFilterGender(value); setPage(1); }}>
              <SelectTrigger className="registry-select w-40">
                <SelectValue placeholder="Gender" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Genders</SelectItem>
                <SelectItem value="Male">Male</SelectItem>
                <SelectItem value="Female">Female</SelectItem>
              </SelectContent>
            </Select>

            <Select value={dataset} onValueChange={(value) => { setDataset(value as DatasetFilter); setPage(1); }}>
              <SelectTrigger className="registry-select w-44">
                <SelectValue placeholder="Dataset" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Registries</SelectItem>
                <SelectItem value="ehvol">EHVol</SelectItem>
                <SelectItem value="bhs">BHS</SelectItem>
              </SelectContent>
            </Select>

            <Badge variant="outline" className="registry-toolbar-status px-3 py-2 text-xs font-medium">
              {activeFilters === 0 ? "No filters applied" : `${activeFilters} filter${activeFilters === 1 ? '' : 's'} applied`}
            </Badge>

            <Button 
              variant="outline" 
              size="sm" 
              className="registry-toolbar-button"
              disabled={selectedPatients.length === 0}
              onClick={handleExport}
            >
              <Download className="h-4 w-4 mr-2" />
              Export ({selectedPatients.length})
            </Button>
          </div>

          {/* Patient Table */}
          <div className="registry-table-shell overflow-hidden rounded-xl border">
            {isLoading ? (
              <div className="flex items-center justify-center p-10">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading patients...</span>
              </div>
            ) : (
            <div className="overflow-x-auto">
            <Table className="registry-table min-w-[78rem]">
              <TableHeader className="registry-table-header">
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
                  <>
                    <tr>
                      <td colSpan={13}>
                        <div
                          ref={tableContainerRef}
                          style={{ height: '500px', overflow: 'auto' }}
                        >
                          <div
                            style={{
                              height: `${rowVirtualizer.getTotalSize()}px`,
                              width: '100%',
                              position: 'relative',
                            }}
                          >
                            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                              const patient = patients[virtualRow.index];
                              return (
                                <TableRow
                                  key={patient.dna_id}
                                  className="registry-row"
                                  style={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    width: '100%',
                                    height: `${virtualRow.size}px`,
                                    transform: `translateY(${virtualRow.start}px)`,
                                  }}
                                >
                                  <TableCell>
                                    <Checkbox
                                      checked={selectedPatients.includes(patient.dna_id)}
                                      onCheckedChange={(checked) => handleSelectPatient(patient.dna_id, checked as boolean)}
                                    />
                                  </TableCell>
                                  <TableCell className="font-mono text-[0.82rem] tracking-[0.08em] uppercase">
                                    <button
                                      onClick={() => onPatientSelect(patient.dna_id)}
                                      className="registry-link cursor-pointer text-[#00a2ddff]"
                                    >
                                      {patient.dna_id}
                                    </button>
                                  </TableCell>
                                  <TableCell>{patient.age ?? <span className="text-muted-foreground/50">—</span>}</TableCell>
                                  <TableCell>{patient.gender ?? <span className="text-muted-foreground/50">—</span>}</TableCell>
                                  <TableCell>{patient.nationality ?? <span className="text-muted-foreground/50">—</span>}</TableCell>
                                  <TableCell>{patient.enrollment_date ? new Date(patient.enrollment_date).toLocaleDateString() : <span className="text-muted-foreground/50">—</span>}</TableCell>
                                  <TableCell>
                                    {patient.systolic_bp && patient.diastolic_bp
                                      ? `${Math.round(Number(patient.systolic_bp))}/${Math.round(Number(patient.diastolic_bp))}`
                                      : <span className="text-muted-foreground/50">—</span>
                                    }
                                  </TableCell>
                                  <TableCell>
                                    {patient.bmi ? Number(patient.bmi).toFixed(1) : <span className="text-muted-foreground/50">—</span>}
                                  </TableCell>
                                  <TableCell>
                                    {patient.echo_ef ? `${patient.echo_ef}%` : <span className="text-muted-foreground/50">—</span>}
                                  </TableCell>
                                  <TableCell>
                                    {patient.mri_ef ? `${patient.mri_ef}%` : <span className="text-muted-foreground/50">—</span>}
                                  </TableCell>
                                  <TableCell>
                                    <div className="flex items-center space-x-2">
                                      <div className="h-2 w-14 rounded-full bg-gray-200/80">
                                        <div
                                          className={`h-2 rounded-full registry-progress-bar ${
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
                                      className="registry-row-action"
                                      onClick={() => onPatientSelect(patient.dna_id)}
                                    >
                                      <Eye className="h-4 w-4" />
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              );
                            })}
                          </div>
                        </div>
                      </td>
                    </tr>
                  </>
                )}
              </TableBody>
            </Table>
            </div>
            )}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-2">
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