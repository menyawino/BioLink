import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Database,
  Users,
  Clock,
  Map,
  BookOpen,
  Activity,
  BarChart3,
  Sparkles,
  ArrowRight,
  Dna,
  TestTube,
  Loader2,
} from "lucide-react";
import logo from "figma:asset/e26cb8b78ee049387f524876448562f480bca21b.png";
import { useRegistryOverview } from "../hooks/useAnalytics";

interface WelcomeScreenProps {
  onNavigate: (view: string) => void;
}

export function WelcomeScreen({
  onNavigate,
}: WelcomeScreenProps) {
  // Fetch real statistics from API
  const { data: overview, isLoading } = useRegistryOverview();
  
  const patientCount = overview?.totalPatients?.toLocaleString() ?? '...';
  const dataCompleteness = overview?.dataCompleteness ?? '...';

  const features = [
    {
      id: "cohort",
      title: "Advanced Cohort Builder",
      description:
        "Create sophisticated patient cohorts with multi-dimensional filtering, temporal constraints, and real-time size estimation.",
      icon: Users,
      badge: "New",
      badgeVariant: "default" as const,
      highlights: [
        "CDC WONDER-style queries",
        "Geographic stratification",
        "Data completeness filtering",
      ],
    },
    {
      id: "analytics",
      title: "Enhanced Registry Analytics",
      description:
        "Advanced data visualization with UpSet plots, timeline exploration, geographic mapping, and comprehensive dashboards.",
      icon: BarChart3,
      badge: "Enhanced",
      badgeVariant: "secondary" as const,
      highlights: [
        "Population analytics",
        "Timeline exploration",
        "Geographic mapping",
        "Outcome visualization",
      ],
    },
    {
      id: "dictionary",
      title: "Comprehensive Data Dictionary",
      description:
        "Complete metadata catalog with variable definitions, quality metrics, clinical context, and data lineage.",
      icon: BookOpen,
      badge: null,
      badgeVariant: null,
      highlights: [
        "Clinical significance notes",
        "Quality assessments",
        "Methodology documentation",
      ],
    },
    {
      id: "charts",
      title: "Interactive Chart Builder",
      description:
        "Create custom visualizations and dynamic charts for research presentations and publications.",
      icon: Activity,
      badge: "Beta",
      badgeVariant: "outline" as const,
      highlights: [
        "Custom visualizations",
        "Export capabilities",
        "Real-time data updates",
      ],
    },
  ];

  const capabilities = [
    "Rich multi-modal data exploration with genomics, biomarkers, and imaging",
    "Powerful cohort formation inspired by CDC WONDER and IHME methodologies",
    "Integrated timeline exploration for longitudinal data analysis",
    "Dynamic geographic visualizations for recruitment and prevalence mapping",
    "Comprehensive data dictionaries with clinical significance and quality metrics",
    "Narrative storytelling components for richer clinical insights",
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center space-x-3">
          <img
            src={logo}
            alt="Magdi Yacoub Heart Foundation"
            className="h-12 w-auto"
          />
          <h1 className="text-3xl font-bold">
            MYF Biolink Platform
          </h1>
          <Badge variant="default" className="text-sm">
            <Sparkles className="h-3 w-3 mr-1" />
            v2.1.0
          </Badge>
        </div>
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
          Comprehensive biomedical data registry with advanced
          precision medicine capabilities, multi-modal data
          integration, and sophisticated research analytics.
        </p>
      </div>

      {/* Key Capabilities */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Platform Capabilities</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {capabilities.map((capability, index) => (
              <div
                key={index}
                className="flex items-start space-x-3"
              >
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                <p className="text-sm">{capability}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card
              key={feature.id}
              className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-105"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <Icon className="h-8 w-8 text-primary" />
                  {feature.badge && (
                    <Badge variant={feature.badgeVariant!}>
                      {feature.badge}
                    </Badge>
                  )}
                </div>
                <CardTitle className="text-lg">
                  {feature.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>

                <div className="space-y-2">
                  {feature.highlights.map(
                    (highlight, index) => (
                      <div
                        key={index}
                        className="flex items-center space-x-2 text-xs"
                      >
                        <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                        <span className="text-muted-foreground">
                          {highlight}
                        </span>
                      </div>
                    ),
                  )}
                </div>

                <Button
                  className="w-full mt-4"
                  variant="outline"
                  onClick={() => onNavigate(feature.id)}
                >
                  Explore Feature
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <p className="text-sm text-muted-foreground">
            Get started with common workflows and data
            exploration tasks
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Button
              variant="default"
              onClick={() => onNavigate("patient")}
            >
              View Patient Profile
            </Button>
            <Button
              variant="outline"
              onClick={() => onNavigate("registry")}
            >
              Browse Registry ({patientCount} patients)
            </Button>
            <Button
              variant="outline"
              onClick={() => onNavigate("cohort")}
            >
              Build New Cohort
            </Button>
            <Button
              variant="outline"
              onClick={() => onNavigate("analytics")}
            >
              View Analytics Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div
              className="text-2xl font-bold"
              style={{ color: "#00a2dd" }}
            >
              {isLoading ? <Loader2 className="h-6 w-6 animate-spin mx-auto" /> : patientCount}
            </div>
            <div className="text-sm text-muted-foreground">
              Total Patients
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div
              className="text-2xl font-bold"
              style={{ color: "#efb01b" }}
            >
              {isLoading ? <Loader2 className="h-6 w-6 animate-spin mx-auto" /> : `${dataCompleteness}%`}
            </div>
            <div className="text-sm text-muted-foreground">
              Data Completeness
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div
              className="text-2xl font-bold"
              style={{ color: "#e9322b" }}
            >
              {overview?.withEcho?.toLocaleString() ?? '...'}
            </div>
            <div className="text-sm text-muted-foreground">
              Echo Studies
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div
              className="text-2xl font-bold"
              style={{ color: "#00a2dd" }}
            >
              {overview?.withMri?.toLocaleString() ?? '...'}
            </div>
            <div className="text-sm text-muted-foreground">
              MRI Studies
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div
              className="text-2xl font-bold"
              style={{ color: "#efb01b" }}
            >
              Live
            </div>
            <div className="text-sm text-muted-foreground">
              Data Refresh
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}