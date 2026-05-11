import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  Database,
  Download,
  ExternalLink,
  FileSearch,
  Filter,
  Link2,
  RefreshCw,
  Search,
  ShieldCheck,
  TableProperties,
} from "lucide-react";

import { API_BASE_URL } from "../api/client";
import type { HarmonizationDictionaryField } from "../api/types";
import { useRegistryOverview } from "../hooks/useAnalytics";
import { useHarmonizationDictionary, useProvenanceSummary } from "../hooks/useHarmonization";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

type CoverageFilter = "all" | "both" | "ehvol" | "bhs" | "unmapped";
type OntologyFilter = "all" | "coded" | "uncoded";

function normalizeTier(tier: string) {
  return tier.trim() || "Unclassified";
}

function titleCaseTier(value: string) {
  return value === "Unclassified" ? value : `Tier ${value}`;
}

function includesInsensitive(value: string, search: string) {
  return value.toLowerCase().includes(search.toLowerCase());
}

function coverageLabel(field: HarmonizationDictionaryField) {
  const hasBhs = Boolean(field.bhs_source);
  const hasEhvol = Boolean(field.ehvol_source);

  if (hasBhs && hasEhvol) return "BHS + EHVol";
  if (hasBhs) return "BHS only";
  if (hasEhvol) return "EHVol only";
  return "Unmapped";
}

function coverageBadgeClass(label: string) {
  if (label === "BHS + EHVol") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (label === "Unmapped") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  return "border-amber-200 bg-amber-50 text-amber-700";
}

function exportRowsToCsv(rows: HarmonizationDictionaryField[]) {
  const headers = [
    "master_col",
    "data_type",
    "tier",
    "unit",
    "bhs_source",
    "ehvol_source",
    "loinc",
    "snomed",
    "allowable_range",
    "phenotype_definition",
  ];

  const escapeCell = (value: string) => `"${value.replace(/"/g, '""')}"`;
  const lines = [headers.join(",")];

  rows.forEach((row) => {
    lines.push(
      headers
        .map((header) => escapeCell(String(row[header as keyof HarmonizationDictionaryField] ?? "")))
        .join(","),
    );
  });

  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `biolink-data-dictionary-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function MetricCard({
  title,
  value,
  hint,
  icon: Icon,
  accentClass,
}: {
  title: string;
  value: string;
  hint: string;
  icon: typeof Database;
  accentClass: string;
}) {
  return (
    <Card className="border-slate-200 bg-gradient-to-br from-white to-slate-50/70">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-600">{title}</p>
            <p className="text-3xl font-semibold tracking-tight">{value}</p>
            <p className="text-sm text-muted-foreground">{hint}</p>
          </div>
          <div className={`rounded-full border p-3 ${accentClass}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function DataDictionary() {
  const [searchTerm, setSearchTerm] = useState("");
  const [tierFilter, setTierFilter] = useState("all");
  const [coverageFilter, setCoverageFilter] = useState<CoverageFilter>("all");
  const [ontologyFilter, setOntologyFilter] = useState<OntologyFilter>("all");
  const [selectedField, setSelectedField] = useState<HarmonizationDictionaryField | null>(null);

  const { data: overview } = useRegistryOverview();
  const {
    data: dictionaryResponse,
    isLoading,
    error,
    refetch,
  } = useHarmonizationDictionary();
  const { data: provenanceSummary } = useProvenanceSummary();

  const dictionaryFields = dictionaryResponse ?? [];
  const totalPatients = overview?.totalPatients?.toLocaleString() ?? "Unavailable";

  useEffect(() => {
    if (!selectedField && dictionaryFields.length > 0) {
      setSelectedField(dictionaryFields[0]);
    }
  }, [dictionaryFields, selectedField]);

  const tierOptions = useMemo(
    () => [
      "all",
      ...Array.from(new Set(dictionaryFields.map((field) => normalizeTier(field.tier)))).sort((left, right) =>
        left.localeCompare(right),
      ),
    ],
    [dictionaryFields],
  );

  const derivedStats = useMemo(() => {
    const mappedInBoth = dictionaryFields.filter((field) => field.bhs_source && field.ehvol_source).length;
    const terminologyMapped = dictionaryFields.filter((field) => field.loinc || field.snomed).length;
    const unitDefined = dictionaryFields.filter((field) => field.unit).length;
    const tierOne = dictionaryFields.filter((field) => normalizeTier(field.tier) === "1").length;
    const perTier = dictionaryFields.reduce<Record<string, number>>((accumulator, field) => {
      const key = normalizeTier(field.tier);
      accumulator[key] = (accumulator[key] ?? 0) + 1;
      return accumulator;
    }, {});

    return {
      mappedInBoth,
      terminologyMapped,
      unitDefined,
      tierOne,
      perTier,
    };
  }, [dictionaryFields]);

  const filteredFields = useMemo(() => {
    return dictionaryFields.filter((field) => {
      const matchesSearch =
        !searchTerm ||
        [
          field.master_col,
          field.data_type,
          field.bhs_source,
          field.ehvol_source,
          field.phenotype_definition,
          field.loinc,
          field.snomed,
          field.allowable_range,
        ].some((value) => includesInsensitive(value, searchTerm));

      const matchesTier = tierFilter === "all" || normalizeTier(field.tier) === tierFilter;

      const hasBhs = Boolean(field.bhs_source);
      const hasEhvol = Boolean(field.ehvol_source);
      const matchesCoverage =
        coverageFilter === "all" ||
        (coverageFilter === "both" && hasBhs && hasEhvol) ||
        (coverageFilter === "bhs" && hasBhs && !hasEhvol) ||
        (coverageFilter === "ehvol" && hasEhvol && !hasBhs) ||
        (coverageFilter === "unmapped" && !hasBhs && !hasEhvol);

      const hasOntology = Boolean(field.loinc || field.snomed);
      const matchesOntology =
        ontologyFilter === "all" ||
        (ontologyFilter === "coded" && hasOntology) ||
        (ontologyFilter === "uncoded" && !hasOntology);

      return matchesSearch && matchesTier && matchesCoverage && matchesOntology;
    });
  }, [coverageFilter, dictionaryFields, ontologyFilter, searchTerm, tierFilter]);

  const activeFilterSummary = useMemo(() => {
    const labels: string[] = [];
    if (tierFilter !== "all") {
      labels.push(titleCaseTier(tierFilter));
    }
    if (coverageFilter !== "all") {
      if (coverageFilter === "both") labels.push("Mapped in both");
      if (coverageFilter === "bhs") labels.push("BHS only");
      if (coverageFilter === "ehvol") labels.push("EHVol only");
      if (coverageFilter === "unmapped") labels.push("Unmapped");
    }
    if (ontologyFilter !== "all") {
      labels.push(ontologyFilter === "coded" ? "Ontology mapped" : "Ontology pending");
    }
    if (searchTerm.trim()) {
      labels.push(`Search: ${searchTerm.trim()}`);
    }
    return labels;
  }, [coverageFilter, ontologyFilter, searchTerm, tierFilter]);

  useEffect(() => {
    if (!selectedField) {
      return;
    }

    const selectedStillVisible = filteredFields.some((field) => field.master_col === selectedField.master_col);
    if (!selectedStillVisible) {
      setSelectedField(filteredFields[0] ?? null);
    }
  }, [filteredFields, selectedField]);

  const topFailureRows = provenanceSummary?.top_failures?.slice(0, 5) ?? [];
  const exportDictionaryUrl = `${API_BASE_URL}/api/harmonization/export?format=csv`;

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-slate-200">
        <CardContent className="space-y-6 p-6 md:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <Badge variant="outline" className="w-fit border-slate-300 bg-white/80 text-slate-700">
                Registry Mapping Workspace
              </Badge>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-slate-700" />
                  <h2 className="text-2xl font-semibold tracking-tight">Real Data Dictionary</h2>
                </div>
                <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
                  This view is generated from the replacement db/test artifacts instead of demo content. It shows the canonical field list,
                  source-to-concept mappings, coverage across BHS and EHVol, and normalization metadata for the live BioLink dataset spanning {totalPatients} patients.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
              <Button variant="outline" asChild>
                <a href={exportDictionaryUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Export Mapping CSV
                </a>
              </Button>
              <Button onClick={() => exportRowsToCsv(filteredFields)} disabled={filteredFields.length === 0}>
                <Download className="mr-2 h-4 w-4" />
                Export Filtered View
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              title="Canonical Fields"
              value={dictionaryFields.length.toLocaleString()}
              hint="Canonical concepts tracked in the replacement registry mapping"
              icon={TableProperties}
              accentClass="border-slate-200 bg-white text-slate-700"
            />
            <MetricCard
              title="Mapped In Both Cohorts"
              value={derivedStats.mappedInBoth.toLocaleString()}
              hint="Fields with both BHS and EHVol source columns present"
              icon={Link2}
              accentClass="border-emerald-200 bg-emerald-50 text-emerald-700"
            />
            <MetricCard
              title="Terminology Linked"
              value={derivedStats.terminologyMapped.toLocaleString()}
              hint="Fields carrying LOINC or SNOMED mappings"
              icon={ShieldCheck}
              accentClass="border-indigo-200 bg-indigo-50 text-indigo-700"
            />
            <MetricCard
              title="Tier 1 Variables"
              value={derivedStats.tierOne.toLocaleString()}
              hint="Concepts shared across both cohorts"
              icon={Database}
              accentClass="border-amber-200 bg-amber-50 text-amber-700"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.6fr_1fr]">
            <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
                <Filter className="h-4 w-4" />
                Filter the live concept catalog
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                <div className="relative md:col-span-2">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder="Search master field, source field, ontology, or phenotype"
                    className="pl-9"
                  />
                </div>

                <Select value={tierFilter} onValueChange={setTierFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Tier" />
                  </SelectTrigger>
                  <SelectContent>
                    {tierOptions.map((tier) => (
                      <SelectItem key={tier} value={tier}>
                        {tier === "all" ? "All tiers" : titleCaseTier(tier)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={coverageFilter} onValueChange={(value: string) => setCoverageFilter(value as CoverageFilter)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Coverage" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All coverage</SelectItem>
                    <SelectItem value="both">Mapped in both</SelectItem>
                    <SelectItem value="ehvol">EHVol only</SelectItem>
                    <SelectItem value="bhs">BHS only</SelectItem>
                    <SelectItem value="unmapped">No source mapping</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-4">
                <Select value={ontologyFilter} onValueChange={(value: string) => setOntologyFilter(value as OntologyFilter)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Ontology coverage" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All ontology states</SelectItem>
                    <SelectItem value="coded">Has LOINC or SNOMED</SelectItem>
                    <SelectItem value="uncoded">No ontology mapping</SelectItem>
                  </SelectContent>
                </Select>

                <div className="rounded-xl border bg-white px-3 py-2 text-sm text-muted-foreground md:col-span-3">
                  Showing <span className="font-medium text-foreground">{filteredFields.length}</span> of <span className="font-medium text-foreground">{dictionaryFields.length}</span> tracked fields
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {activeFilterSummary.length === 0 ? (
                  <Badge variant="outline" className="border-slate-200 bg-white text-slate-600">
                    No active filters
                  </Badge>
                ) : (
                  activeFilterSummary.map((summary) => (
                    <Badge key={summary} variant="outline" className="border-slate-200 bg-white text-slate-700">
                      {summary}
                    </Badge>
                  ))
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
                <ShieldCheck className="h-4 w-4" />
                Trust boundaries
              </div>
              <div className="space-y-3 text-sm text-muted-foreground">
                <p>This tab only reports metadata that exists in the backend harmonization tables.</p>
                <p>Clinical interpretation is intentionally limited to stored phenotype definitions and allowable ranges.</p>
                <p>Gaps in ontology mapping or source linkage are surfaced as work items instead of being hidden behind placeholder content.</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {error ? (
        <Card className="border-red-200 bg-red-50/60">
          <CardContent className="flex items-start gap-3 p-5 text-sm text-red-900">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <div className="space-y-1">
              <p className="font-medium">The data dictionary could not be loaded.</p>
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <Tabs defaultValue="catalog" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 md:w-[520px]">
          <TabsTrigger value="catalog">Field Catalog</TabsTrigger>
          <TabsTrigger value="quality">Quality Signals</TabsTrigger>
          <TabsTrigger value="guide">Usage Guide</TabsTrigger>
        </TabsList>

        <TabsContent value="catalog" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.55fr_1fr]">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileSearch className="h-4 w-4" />
                  Live harmonization catalog
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[560px] overflow-auto md:h-[720px]">
                  <Table>
                    <TableHeader className="sticky top-0 bg-background">
                      <TableRow>
                        <TableHead>Field</TableHead>
                        <TableHead>Tier</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Source Coverage</TableHead>
                        <TableHead>Ontology</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {isLoading ? (
                        <TableRow>
                          <TableCell colSpan={5} className="h-24 text-center text-sm text-muted-foreground">
                            Loading harmonization dictionary...
                          </TableCell>
                        </TableRow>
                      ) : filteredFields.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="h-24 text-center text-sm text-muted-foreground">
                            No fields match the current filters.
                          </TableCell>
                        </TableRow>
                      ) : (
                        filteredFields.map((field) => {
                          const isSelected = selectedField?.master_col === field.master_col;
                          const hasOntology = Boolean(field.loinc || field.snomed);
                          const fieldCoverageLabel = coverageLabel(field);

                          return (
                            <TableRow
                              key={field.master_col}
                              className={`cursor-pointer transition-colors hover:bg-slate-50/80 ${isSelected ? "bg-slate-50" : ""}`}
                              onClick={() => setSelectedField(field)}
                            >
                              <TableCell>
                                <div className="space-y-1">
                                  <div className="font-medium">{field.master_col}</div>
                                  <div className="text-xs text-muted-foreground line-clamp-2">
                                    {field.phenotype_definition || "No phenotype definition recorded yet."}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">{normalizeTier(field.tier)}</Badge>
                              </TableCell>
                              <TableCell>{field.data_type || "Unknown"}</TableCell>
                              <TableCell>
                                <Badge variant="outline" className={coverageBadgeClass(fieldCoverageLabel)}>{fieldCoverageLabel}</Badge>
                              </TableCell>
                              <TableCell>
                                {hasOntology ? (
                                  <div className="flex flex-wrap gap-1">
                                    {field.loinc ? <Badge variant="outline" className="border-indigo-200 bg-indigo-50 text-indigo-700">LOINC</Badge> : null}
                                    {field.snomed ? <Badge variant="outline" className="border-violet-200 bg-violet-50 text-violet-700">SNOMED</Badge> : null}
                                  </div>
                                ) : (
                                  <span className="text-xs text-amber-700">Pending</span>
                                )}
                              </TableCell>
                            </TableRow>
                          );
                        })
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <Card className="xl:sticky xl:top-6 xl:h-fit">
              <CardHeader>
                <CardTitle className="text-base">{selectedField ? selectedField.master_col : "Select a field"}</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedField ? (
                  <div className="space-y-5">
                    <div className="space-y-2">
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="outline">{titleCaseTier(normalizeTier(selectedField.tier))}</Badge>
                        <Badge variant="secondary">{selectedField.data_type || "Unknown type"}</Badge>
                        {selectedField.unit ? <Badge variant="outline">Unit: {selectedField.unit}</Badge> : null}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {selectedField.phenotype_definition || "No phenotype definition is stored for this field yet."}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 gap-4 rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
                      <div>
                        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Master Column</Label>
                        <p className="mt-1 font-medium">{selectedField.master_col}</p>
                      </div>
                      <div>
                        <Label className="text-xs uppercase tracking-wide text-muted-foreground">Allowable Range</Label>
                        <p className="mt-1 text-sm">{selectedField.allowable_range || "Not defined"}</p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <h3 className="text-sm font-medium">Source mapping</h3>
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        <div className="rounded-xl border border-slate-200 bg-white p-4">
                          <Label className="text-xs uppercase tracking-wide text-muted-foreground">BHS Source</Label>
                          <p className="mt-2 break-words text-sm">{selectedField.bhs_source || "No BHS source mapped"}</p>
                        </div>
                        <div className="rounded-xl border border-slate-200 bg-white p-4">
                          <Label className="text-xs uppercase tracking-wide text-muted-foreground">EHVol Source</Label>
                          <p className="mt-2 break-words text-sm">{selectedField.ehvol_source || "No EHVol source mapped"}</p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <h3 className="text-sm font-medium">Terminology alignment</h3>
                      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        <div className="rounded-xl border border-slate-200 bg-white p-4">
                          <Label className="text-xs uppercase tracking-wide text-muted-foreground">LOINC</Label>
                          <p className="mt-2 break-words text-sm">{selectedField.loinc || "No LOINC code recorded"}</p>
                        </div>
                        <div className="rounded-xl border border-slate-200 bg-white p-4">
                          <Label className="text-xs uppercase tracking-wide text-muted-foreground">SNOMED</Label>
                          <p className="mt-2 break-words text-sm">{selectedField.snomed || "No SNOMED code recorded"}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-12 text-center text-sm text-muted-foreground">
                    Select a field from the table to inspect its actual source mappings and terminology coverage.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="quality" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.1fr_1fr]">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Coverage and modeling signals</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="rounded-2xl border p-4">
                    <p className="text-sm text-muted-foreground">Fields with units</p>
                    <p className="mt-2 text-2xl font-semibold">{derivedStats.unitDefined}</p>
                    <p className="mt-1 text-sm text-muted-foreground">Explicit unit metadata carried forward from the step_7 mapping outputs.</p>
                  </div>
                  <div className="rounded-2xl border p-4">
                    <p className="text-sm text-muted-foreground">Concepts tracked in coverage audit</p>
                    <p className="mt-2 text-2xl font-semibold">{provenanceSummary?.columns_tracked ?? 0}</p>
                    <p className="mt-1 text-sm text-muted-foreground">Canonical concepts measured in the unification audit.</p>
                  </div>
                </div>

                <div className="rounded-2xl border p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium">Coverage tier distribution</p>
                      <p className="text-sm text-muted-foreground">How the current concept catalog is split between shared and single-cohort mappings.</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {Object.entries(derivedStats.perTier)
                      .sort(([left], [right]) => left.localeCompare(right))
                      .map(([tier, count]) => {
                        const percentage = dictionaryFields.length > 0 ? Math.round((count / dictionaryFields.length) * 100) : 0;
                        return (
                          <div key={tier} className="space-y-1">
                            <div className="flex items-center justify-between text-sm">
                              <span>{titleCaseTier(tier)}</span>
                              <span className="text-muted-foreground">{count} fields</span>
                            </div>
                            <div className="h-2 rounded-full bg-slate-100">
                              <div className="h-2 rounded-full bg-slate-700" style={{ width: `${percentage}%` }} />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Coverage audit</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-2xl border p-4 text-center">
                    <p className="text-sm text-muted-foreground">Tracked</p>
                    <p className="mt-2 text-2xl font-semibold">{provenanceSummary?.total_records ?? 0}</p>
                  </div>
                  <div className="rounded-2xl border p-4 text-center">
                    <p className="text-sm text-muted-foreground">Shared</p>
                    <p className="mt-2 text-2xl font-semibold text-emerald-700">{provenanceSummary?.pass_count ?? 0}</p>
                  </div>
                  <div className="rounded-2xl border p-4 text-center">
                    <p className="text-sm text-muted-foreground">Single cohort</p>
                    <p className="mt-2 text-2xl font-semibold text-red-700">{provenanceSummary?.fail_count ?? 0}</p>
                  </div>
                </div>

                <div className="rounded-2xl border p-4">
                  <p className="font-medium">Top coverage gaps</p>
                  <div className="mt-3 space-y-3">
                    {topFailureRows.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No single-cohort coverage gaps are currently available.</p>
                    ) : (
                      topFailureRows.map((failure) => (
                        <div key={`${failure.master_col}-${failure.reason}`} className="rounded-xl bg-slate-50 p-3">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-medium">{failure.master_col}</p>
                              <p className="mt-1 text-sm text-muted-foreground">{failure.reason || "No coverage note recorded"}</p>
                            </div>
                            <Badge variant="outline">{failure.count}</Badge>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="guide" className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">How to read this page</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p><span className="font-medium text-foreground">Master column</span> is the canonical BioLink concept used in the unified registry snapshot.</p>
                <p><span className="font-medium text-foreground">Source mapping</span> shows the original BHS and EHVol columns that feed that concept.</p>
                <p><span className="font-medium text-foreground">Coverage tier</span> separates shared concepts from dataset-specific concepts that still need interpretation.</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recommended next cleanup</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>Prioritize shared Tier 1 concepts so high-value variables have consistent cross-cohort definitions.</p>
                <p>Review single-cohort mappings to decide whether they are legitimate registry differences or candidates for new canonical concepts.</p>
                <p>Use the coverage gap list to guide the next db/test unification pass before expanding documentation.</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Current tier counts</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Object.entries(derivedStats.perTier)
                  .sort(([left], [right]) => left.localeCompare(right))
                  .map(([tier, count]) => (
                    <div key={tier} className="flex items-center justify-between rounded-xl border px-3 py-2 text-sm">
                      <span>{titleCaseTier(tier)}</span>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
