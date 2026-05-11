import { useEffect, useState } from "react";
import { motion, useInView } from "framer-motion";
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
      title: "Advanced Registry Analytics",
      description:
        "Advanced data visualization with UpSet plots, timeline exploration, geographic mapping, and comprehensive dashboards.",
      icon: BarChart3,
      badge: "Updated",
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

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.08, delayChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
  };

  const cardHover = {
    scale: 1.02,
    y: -4,
    transition: { duration: 0.2 },
  };

  // Animated counter hook
  function useAnimatedCounter(target: number, duration = 1500) {
    const [count, setCount] = useState(0);
    useEffect(() => {
      if (!target) return;
      let start = 0;
      const step = (timestamp: number) => {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
        setCount(Math.floor(progress * target));
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }, [target, duration]);
    return count;
  }

  const animatedPatientCount = useAnimatedCounter(overview?.totalPatients || 0);
  const animatedCompleteness = useAnimatedCounter(overview?.dataCompleteness || 0);

  return (
    <motion.div
      className="space-y-8"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Header */}
      <motion.div className="text-center space-y-4" variants={itemVariants}>
        <div className="flex items-center justify-center space-x-3">
          <motion.img
            src={logo}
            alt="Magdi Yacoub Heart Foundation"
            className="h-12 w-auto"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
          />
          <motion.h1
            className="text-3xl font-bold"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            MYF Biolink Platform
          </motion.h1>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 20, delay: 0.2 }}
          >
            <Badge variant="default" className="text-sm">
              <Sparkles className="h-3 w-3 mr-1" />
              v2.1.0
            </Badge>
          </motion.div>
        </div>
        <motion.p
          className="text-lg text-muted-foreground max-w-3xl mx-auto"
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          Comprehensive biomedical data registry with advanced
          precision medicine capabilities, multi-modal data
          integration, and sophisticated research analytics.
        </motion.p>
      </motion.div>

      {/* Key Capabilities */}
      <motion.div variants={itemVariants}>
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
                <motion.div
                  key={index}
                  className="flex items-start space-x-3"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.06 }}
                >
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                  <p className="text-sm">{capability}</p>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Feature Grid */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        variants={containerVariants}
      >
        {features.map((feature, idx) => {
          const Icon = feature.icon;
          return (
            <motion.div
              key={feature.id}
              variants={itemVariants}
              whileHover={cardHover}
            >
              <Card
                className="cursor-pointer hover:shadow-lg transition-shadow duration-200 h-full"
                onClick={() => onNavigate(feature.id)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <motion.div
                      whileHover={{ rotate: 5, scale: 1.1 }}
                      transition={{ type: "spring", stiffness: 300 }}
                    >
                      <Icon className="h-8 w-8 text-primary" />
                    </motion.div>
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
                        <motion.div
                          key={index}
                          className="flex items-center space-x-2 text-xs"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.5 + idx * 0.1 + index * 0.05 }}
                        >
                          <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                          <span className="text-muted-foreground">
                            {highlight}
                          </span>
                        </motion.div>
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
            </motion.div>
          );
        })}
      </motion.div>

      {/* Quick Actions */}
      <motion.div variants={itemVariants}>
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
              {[
                { label: "View Patient Profile", view: "patient", variant: "default" as const },
                { label: `Browse Registry (${patientCount} patients)`, view: "registry", variant: "outline" as const },
                { label: "Build New Cohort", view: "cohort", variant: "outline" as const },
                { label: "View Analytics Dashboard", view: "analytics", variant: "outline" as const },
              ].map((action, idx) => (
                <motion.div
                  key={action.view}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 + idx * 0.08 }}
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                >
                  <Button
                    variant={action.variant}
                    onClick={() => onNavigate(action.view)}
                    className="w-full"
                  >
                    {action.label}
                  </Button>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats Summary */}
      <motion.div
        className="grid grid-cols-2 md:grid-cols-5 gap-4"
        variants={containerVariants}
      >
        <motion.div variants={itemVariants}>
          <Card>
            <CardContent className="p-4 text-center">
              <div
                className="text-2xl font-bold"
                style={{ color: "#00a2dd" }}
              >
                {isLoading ? <Loader2 className="h-6 w-6 animate-spin mx-auto" /> : animatedPatientCount.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">
                Total Patients
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={itemVariants}>
          <Card>
            <CardContent className="p-4 text-center">
              <div
                className="text-2xl font-bold"
                style={{ color: "#efb01b" }}
              >
                {isLoading ? <Loader2 className="h-6 w-6 animate-spin mx-auto" /> : `${animatedCompleteness}%`}
              </div>
              <div className="text-sm text-muted-foreground">
                Data Completeness
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={itemVariants}>
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
        </motion.div>
        <motion.div variants={itemVariants}>
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
        </motion.div>
        <motion.div variants={itemVariants}>
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
        </motion.div>
      </motion.div>
    </motion.div>
  );
}