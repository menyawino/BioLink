import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { FileText, ExternalLink, Download, Users, Calendar, BarChart, TrendingUp, Book, Award, Link as LinkIcon } from "lucide-react";
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

interface Publication {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  year: number;
  type: 'original' | 'review' | 'meta-analysis' | 'editorial' | 'case-report';
  status: 'published' | 'accepted' | 'under-review' | 'in-preparation';
  impactFactor: number;
  citations: number;
  doi?: string;
  pmid?: string;
  dataUsed: string[];
  cohortsUsed: string[];
  fundingSource: string[];
  abstract: string;
  keyFindings: string[];
  clinicalImplications: string;
  mediaAttention: number;
  altmetricScore: number;
}

export function PublicationsTracker() {
  const [selectedYear, setSelectedYear] = useState("all");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedPublication, setSelectedPublication] = useState<Publication | null>(null);

  const publications: Publication[] = [
    {
      id: "pub_001",
      title: "Machine Learning Approaches for Cardiovascular Risk Prediction Using Multi-Modal Registry Data",
      authors: ["Johnson, S.M.", "Chen, L.", "Rodriguez, A.", "Kim, J.H."],
      journal: "Nature Medicine",
      year: 2024,
      type: "original",
      status: "published",
      impactFactor: 87.2,
      citations: 23,
      doi: "10.1038/s41591-024-01234-x",
      pmid: "38123456",
      dataUsed: ["Genomics", "Biomarkers", "Clinical Variables", "Imaging"],
      cohortsUsed: ["Primary CVD Cohort", "Genomics Subset"],
      fundingSource: ["NIH R01", "American Heart Association"],
      abstract: "We developed and validated machine learning models using comprehensive multi-modal data from 1,247 cardiovascular disease patients...",
      keyFindings: [
        "ML models achieved 0.85 AUC for 5-year mortality prediction",
        "Genomic data improved prediction by 12% over clinical variables alone",
        "Novel biomarkers identified as key predictors"
      ],
      clinicalImplications: "These findings suggest that integrated multi-modal approaches can significantly improve cardiovascular risk stratification in clinical practice.",
      mediaAttention: 8,
      altmetricScore: 156
    },
    {
      id: "pub_002", 
      title: "Geographic Disparities in Cardiovascular Disease Outcomes: A Multi-Center Registry Analysis",
      authors: ["Martinez, R.", "Thompson, K.L.", "Johnson, S.M.", "Patel, N."],
      journal: "Circulation",
      year: 2024,
      type: "original",
      status: "published",
      impactFactor: 25.8,
      citations: 15,
      doi: "10.1161/CIRCULATIONAHA.124.012345",
      pmid: "38234567",
      dataUsed: ["Demographics", "Outcomes", "Geographic Data"],
      cohortsUsed: ["Multi-Center Cohort"],
      fundingSource: ["CDC Grant", "Regional Health Initiative"],
      abstract: "This study examined geographic variations in cardiovascular disease outcomes across four major US regions...",
      keyFindings: [
        "Southeast region showed 40% higher mortality rates",
        "Rural areas had delayed time to treatment",
        "Socioeconomic factors mediated regional differences"
      ],
      clinicalImplications: "Results highlight the need for targeted interventions in high-risk geographic regions and improved access to specialized care.",
      mediaAttention: 12,
      altmetricScore: 203
    },
    {
      id: "pub_003",
      title: "Novel Biomarkers in Heart Failure: Longitudinal Analysis from the CVD Registry",
      authors: ["Chen, L.", "Williams, M.D.", "Johnson, S.M."],
      journal: "Journal of the American College of Cardiology",
      year: 2023,
      type: "original",
      status: "published",
      impactFactor: 24.4,
      citations: 67,
      doi: "10.1016/j.jacc.2023.01.234",
      pmid: "37123456",
      dataUsed: ["Biomarkers", "Clinical Variables", "Longitudinal Data"],
      cohortsUsed: ["Heart Failure Cohort"],
      fundingSource: ["NIH K08", "Heart Failure Society Grant"],
      abstract: "We conducted a comprehensive analysis of novel cardiac biomarkers in heart failure patients over 24 months...",
      keyFindings: [
        "Galectin-3 levels predicted readmission with 78% accuracy",
        "ST2 showed strong correlation with clinical outcomes",
        "Combined protein biomarker panel outperformed individual markers"
      ],
      clinicalImplications: "These novel biomarkers could be incorporated into clinical decision-making algorithms for heart failure management.",
      mediaAttention: 6,
      altmetricScore: 134
    },
    {
      id: "pub_004",
      title: "Pharmacogenomics-Guided Therapy in Cardiovascular Disease: Registry-Based Implementation Study",
      authors: ["Kim, J.H.", "Rodriguez, A.", "Johnson, S.M.", "Lee, Y."],
      journal: "Pharmacogenomics",
      year: 2024,
      type: "original",
      status: "under-review",
      impactFactor: 4.8,
      citations: 0,
      dataUsed: ["Genomics", "Medications", "Outcomes"],
      cohortsUsed: ["Pharmacogenomics Cohort"],
      fundingSource: ["Precision Medicine Initiative"],
      abstract: "This implementation study evaluated the clinical utility of pharmacogenomics-guided prescribing in cardiovascular patients...",
      keyFindings: [
        "30% reduction in adverse drug reactions",
        "Improved medication adherence with genetic testing",
        "Cost-effectiveness demonstrated over 12 months"
      ],
      clinicalImplications: "Routine pharmacogenomic testing could improve medication safety and efficacy in cardiovascular care.",
      mediaAttention: 0,
      altmetricScore: 0
    },
    {
      id: "pub_005",
      title: "Integration of Multi-Modal Imaging in Cardiovascular Risk Assessment: A Registry Perspective",
      authors: ["Patel, N.", "Thompson, K.L.", "Johnson, S.M."],
      journal: "European Heart Journal",
      year: 2024,
      type: "review",
      status: "accepted",
      impactFactor: 35.3,
      citations: 0,
      dataUsed: ["Imaging", "Clinical Variables"],
      cohortsUsed: ["Imaging Cohort"],
      fundingSource: ["European Society of Cardiology Grant"],
      abstract: "This comprehensive review examines the role of multi-modal imaging approaches in cardiovascular risk assessment...",
      keyFindings: [
        "CT angiography combined with functional testing improves accuracy",
        "AI-enhanced imaging analysis shows promise",
        "Cost considerations limit widespread adoption"
      ],
      clinicalImplications: "Strategic implementation of multi-modal imaging could optimize patient selection and improve outcomes.",
      mediaAttention: 0,
      altmetricScore: 0
    }
  ];

  const publicationsByYear = [
    { year: 2020, count: 2, citations: 45 },
    { year: 2021, count: 4, citations: 78 },
    { year: 2022, count: 3, citations: 92 },
    { year: 2023, count: 5, citations: 134 },
    { year: 2024, count: 8, citations: 89 }
  ];

  const publicationsByType = [
    { type: "Original Research", count: 12, color: "#3b82f6" },
    { type: "Review Articles", count: 6, color: "#22c55e" },
    { type: "Meta-Analysis", count: 2, color: "#f59e0b" },
    { type: "Case Reports", count: 3, color: "#ef4444" }
  ];

  const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

  const filteredPublications = publications.filter(pub => {
    const matchesSearch = pub.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         pub.authors.some(author => author.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesYear = selectedYear === "all" || pub.year.toString() === selectedYear;
    const matchesType = selectedType === "all" || pub.type === selectedType;
    const matchesStatus = selectedStatus === "all" || pub.status === selectedStatus;
    
    return matchesSearch && matchesYear && matchesType && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800';
      case 'accepted': return 'bg-blue-100 text-blue-800';
      case 'under-review': return 'bg-yellow-100 text-yellow-800';
      case 'in-preparation': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'original': return '📊';
      case 'review': return '📚';
      case 'meta-analysis': return '🔍';
      case 'editorial': return '✍️';
      case 'case-report': return '📋';
      default: return '📄';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Publications & Research Impact Tracker</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Track research outputs, citations, and real-world impact of registry-based studies
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Input
                placeholder="Search publications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger>
                <SelectValue placeholder="All years" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Years</SelectItem>
                <SelectItem value="2024">2024</SelectItem>
                <SelectItem value="2023">2023</SelectItem>
                <SelectItem value="2022">2022</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger>
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="original">Original Research</SelectItem>
                <SelectItem value="review">Review Articles</SelectItem>
                <SelectItem value="meta-analysis">Meta-Analysis</SelectItem>
              </SelectContent>
            </Select>

            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="under-review">Under Review</SelectItem>
                <SelectItem value="in-preparation">In Preparation</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Publications</p>
                    <p className="text-2xl">{publications.length}</p>
                  </div>
                  <Book className="h-8 w-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Citations</p>
                    <p className="text-2xl">{publications.reduce((sum, p) => sum + p.citations, 0)}</p>
                  </div>
                  <Award className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Impact Factor</p>
                    <p className="text-2xl">
                      {(publications.reduce((sum, p) => sum + p.impactFactor, 0) / publications.length).toFixed(1)}
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">H-Index</p>
                    <p className="text-2xl">18</p>
                  </div>
                  <BarChart className="h-8 w-8 text-orange-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Publications List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Recent Publications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {filteredPublications.map((publication) => (
              <Card key={publication.id} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardContent className="p-4" onClick={() => setSelectedPublication(publication)}>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <span className="text-2xl">{getTypeIcon(publication.type)}</span>
                      <div className="flex-1">
                        <h3 className="font-medium leading-tight mb-2">{publication.title}</h3>
                        <p className="text-sm text-muted-foreground mb-2">
                          {publication.authors.slice(0, 3).join(", ")}
                          {publication.authors.length > 3 && ` et al.`}
                        </p>
                        <div className="flex items-center space-x-4 text-sm">
                          <span className="font-medium">{publication.journal}</span>
                          <span>{publication.year}</span>
                          <Badge className={getStatusColor(publication.status)}>
                            {publication.status.replace('-', ' ')}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>IF: {publication.impactFactor}</span>
                        <span>Citations: {publication.citations}</span>
                        {publication.altmetricScore > 0 && (
                          <span>Altmetric: {publication.altmetricScore}</span>
                        )}
                      </div>
                      
                      <div className="flex space-x-2">
                        {publication.doi && (
                          <Button variant="ghost" size="sm">
                            <LinkIcon className="h-4 w-4" />
                          </Button>
                        )}
                        <Button variant="ghost" size="sm">
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>

        {/* Publication Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {selectedPublication ? "Publication Details" : "Select Publication"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedPublication ? (
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium mb-2">{selectedPublication.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {selectedPublication.authors.join(", ")}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <Label className="text-xs font-medium text-muted-foreground">Journal</Label>
                    <p>{selectedPublication.journal}</p>
                  </div>
                  <div>
                    <Label className="text-xs font-medium text-muted-foreground">Year</Label>
                    <p>{selectedPublication.year}</p>
                  </div>
                  <div>
                    <Label className="text-xs font-medium text-muted-foreground">Impact Factor</Label>
                    <p>{selectedPublication.impactFactor}</p>
                  </div>
                  <div>
                    <Label className="text-xs font-medium text-muted-foreground">Citations</Label>
                    <p>{selectedPublication.citations}</p>
                  </div>
                </div>

                {selectedPublication.doi && (
                  <div>
                    <Label className="text-xs font-medium text-muted-foreground">DOI</Label>
                    <p className="text-sm font-mono">{selectedPublication.doi}</p>
                  </div>
                )}

                <div>
                  <Label className="text-xs font-medium text-muted-foreground">Data Sources Used</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedPublication.dataUsed.map((data) => (
                      <Badge key={data} variant="outline" className="text-xs">
                        {data}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-xs font-medium text-muted-foreground">Key Findings</Label>
                  <ul className="text-sm mt-1 space-y-1">
                    {selectedPublication.keyFindings.map((finding, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-blue-500 mt-1">•</span>
                        <span>{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <Label className="text-xs font-medium text-muted-foreground">Clinical Implications</Label>
                  <p className="text-sm mt-1">{selectedPublication.clinicalImplications}</p>
                </div>

                {selectedPublication.mediaAttention > 0 && (
                  <div>
                    <Label className="text-xs font-medium text-muted-foreground">Media Coverage</Label>
                    <p className="text-sm mt-1">{selectedPublication.mediaAttention} media mentions</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a publication to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Publications Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RechartsBarChart data={publicationsByYear}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" name="Publications" />
              </RechartsBarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Publication Types</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={publicationsByType}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="count"
                  nameKey="type"
                >
                  {publicationsByType.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}