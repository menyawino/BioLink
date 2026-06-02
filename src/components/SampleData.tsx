import { useMemo, useState } from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Dna, FileArchive, FlaskConical, Microscope } from "lucide-react";
import type { GenomicData } from "../api/types";

interface SampleDataProps {
  patientId: string;
  enrollmentDate?: string | null;
  genomicData?: GenomicData;
}

type AnalysisConfig = {
  genome: string;
  panel: string;
  priority: string;
};

function hasSequencingSignals(genomicData?: GenomicData) {
  if (!genomicData) {
    return false;
  }

  const hasScores = Object.values(genomicData.polygenic).some((value) => value > 0);
  const hasAncestry = Object.values(genomicData.ancestry).some((value) => value > 0);
  return hasScores || hasAncestry || genomicData.variants.length > 0 || genomicData.pharmacogenomics.length > 0;
}

export function SampleData({ patientId, enrollmentDate, genomicData }: SampleDataProps) {
  const sequencingDone = hasSequencingSignals(genomicData);
  const analysisAlreadyAvailable = Boolean(genomicData && (genomicData.variants.length > 0 || genomicData.pharmacogenomics.length > 0));
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const [isAnalyzed, setIsAnalyzed] = useState(analysisAlreadyAvailable);
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfig>({
    genome: "GRCh38",
    panel: "Cardiomyopathy",
    priority: analysisAlreadyAvailable ? "Routine" : "High",
  });

  const fastqDetails = useMemo(() => {
    if (!sequencingDone) {
      return {
        status: "Awaiting FASTQ upload",
        fileName: "No FASTQ attached",
        readLength: "-",
        size: "-",
        instrument: "-",
        lane: "-",
      };
    }

    const variantCount = genomicData?.variants.length ?? 0;
    const pgxCount = genomicData?.pharmacogenomics.length ?? 0;
    const estimatedGb = Math.max(3.8, Number((4.2 + variantCount * 0.15 + pgxCount * 0.08).toFixed(1)));

    return {
      status: "FASTQ ready",
      fileName: `${patientId}_tumor_R1.fastq.gz / ${patientId}_tumor_R2.fastq.gz`,
      readLength: variantCount > 3 ? "2 x 150 bp" : "2 x 100 bp",
      size: `${estimatedGb} GB`,
      instrument: "NovaSeq 6000",
      lane: sequencingDone ? "L004" : "-",
    };
  }, [genomicData, patientId, sequencingDone]);

  const handleAnalyze = () => {
    if (!sequencingDone) {
      return;
    }

    setIsAnalyzed(true);
    setAnalysisOpen(false);
  };

  const statusBadge = (done: boolean, readyLabel: string, pendingLabel: string) => (
    <Badge variant={done ? "secondary" : "outline"} className={done ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-100" : "text-amber-700"}>
      {done ? readyLabel : pendingLabel}
    </Badge>
  );

  return (
    <>
      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Dna className="h-5 w-5 text-cyan-600" />
              Sample Processing
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Sample ID</p>
                <p className="mt-1 font-medium">{patientId}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Collected</p>
                <p className="mt-1 font-medium">{enrollmentDate || "Not recorded"}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">DNA sequencing</p>
                <div className="mt-2">{statusBadge(sequencingDone, "Completed", "Not done")}</div>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Analysis</p>
                <div className="mt-2">{statusBadge(isAnalyzed, "Analyzed", "Pending")}</div>
              </div>
            </div>

            <div className="rounded-xl border border-dashed p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">Current FASTQ package</p>
                  <p className="mt-1 text-sm text-muted-foreground">{fastqDetails.fileName}</p>
                </div>
                <Button onClick={() => setAnalysisOpen(true)}>Analyze Sample</Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Microscope className="h-5 w-5 text-violet-600" />
              Run Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3 rounded-lg border p-4">
              <FileArchive className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="font-medium">FASTQ status</p>
                <p className="text-sm text-muted-foreground">{fastqDetails.status}</p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg border p-4">
              <FlaskConical className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="font-medium">Configured analysis</p>
                <p className="text-sm text-muted-foreground">
                  {analysisConfig.genome} genome, {analysisConfig.panel} panel, {analysisConfig.priority.toLowerCase()} priority
                </p>
              </div>
            </div>
            <div className="rounded-lg bg-muted/40 p-4 text-sm text-muted-foreground">
              This tab is intentionally lightweight. It surfaces whether sequencing exists, whether interpretation has been run, and a stub workflow entry point for analysis configuration.
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={analysisOpen} onOpenChange={setAnalysisOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Analyze sample {patientId}</DialogTitle>
            <DialogDescription>
              Review the current FASTQ package and choose a small set of analysis parameters before starting the run.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-6 py-2 md:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-3 rounded-xl border p-4">
              <h3 className="font-medium">FASTQ details</h3>
              <div className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <p className="text-muted-foreground">File pair</p>
                  <p className="mt-1 break-words font-medium">{fastqDetails.fileName}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <p className="mt-1 font-medium">{fastqDetails.status}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Read length</p>
                  <p className="mt-1 font-medium">{fastqDetails.readLength}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Size</p>
                  <p className="mt-1 font-medium">{fastqDetails.size}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Instrument</p>
                  <p className="mt-1 font-medium">{fastqDetails.instrument}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Lane</p>
                  <p className="mt-1 font-medium">{fastqDetails.lane}</p>
                </div>
              </div>
            </div>

            <div className="space-y-4 rounded-xl border p-4">
              <h3 className="font-medium">Parameters</h3>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Genome</p>
                <Select value={analysisConfig.genome} onValueChange={(value) => setAnalysisConfig((current) => ({ ...current, genome: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select genome" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GRCh38">GRCh38</SelectItem>
                    <SelectItem value="GRCh37">GRCh37</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Panel</p>
                <Select value={analysisConfig.panel} onValueChange={(value) => setAnalysisConfig((current) => ({ ...current, panel: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select panel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Cardiomyopathy">Cardiomyopathy</SelectItem>
                    <SelectItem value="Arrhythmia">Arrhythmia</SelectItem>
                    <SelectItem value="Whole genome">Whole genome</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Priority</p>
                <Select value={analysisConfig.priority} onValueChange={(value) => setAnalysisConfig((current) => ({ ...current, priority: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select priority" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Routine">Routine</SelectItem>
                    <SelectItem value="High">High</SelectItem>
                    <SelectItem value="Urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setAnalysisOpen(false)}>Close</Button>
            <Button onClick={handleAnalyze} disabled={!sequencingDone}>Start Analysis</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}