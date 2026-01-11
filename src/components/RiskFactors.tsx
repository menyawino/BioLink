import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { CheckCircle, XCircle, Target, Activity, Cigarette } from "lucide-react";
import { ASCVDRiskCalculator } from "./ASCVDRiskCalculator";

interface RiskFactorsProps {
  riskFactors: {
    hypertension: boolean;
    diabetes: boolean;
    smoking: boolean;
    familyHistory: boolean;
    obesity: boolean;
    sedentary: boolean;
    age: number;
    bmi: number;
  };
}

export function RiskFactors({ riskFactors }: RiskFactorsProps) {
  const getRiskIcon = (hasRisk: boolean) => {
    return hasRisk ? (
      <XCircle className="h-4 w-4 text-red-500" />
    ) : (
      <CheckCircle className="h-4 w-4 text-green-500" />
    );
  };

  const getBMIStatus = (bmi: number) => {
    if (bmi >= 30) return { status: 'Obese', variant: 'destructive' as const, color: 'red' };
    if (bmi >= 25) return { status: 'Overweight', variant: 'default' as const, color: 'orange' };
    if (bmi >= 18.5) return { status: 'Normal', variant: 'secondary' as const, color: 'green' };
    return { status: 'Underweight', variant: 'outline' as const, color: 'blue' };
  };

  const bmiStatus = getBMIStatus(riskFactors.bmi);

  const riskCount = [
    riskFactors.hypertension,
    riskFactors.diabetes,
    riskFactors.smoking,
    riskFactors.familyHistory,
    riskFactors.obesity,
    riskFactors.sedentary
  ].filter(Boolean).length;

  return (
    <Tabs defaultValue="factors" className="space-y-4">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="factors">Risk Factors</TabsTrigger>
        <TabsTrigger value="ascvd">ASCVD Calculator</TabsTrigger>
      </TabsList>

      <TabsContent value="factors">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>Risk Assessment Summary</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-3xl mb-1">
                    {riskCount}/6
                  </div>
                  <p className="text-sm text-muted-foreground">Risk Factors Present</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl mb-1">{riskFactors.bmi}</div>
                  <p className="text-sm text-muted-foreground">BMI</p>
                  <Badge variant={bmiStatus.variant} className="mt-1">
                    {bmiStatus.status}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cardiovascular Risk Factors</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getRiskIcon(riskFactors.hypertension)}
                  <span>Hypertension</span>
                </div>
                <Badge variant={riskFactors.hypertension ? 'destructive' : 'secondary'}>
                  {riskFactors.hypertension ? 'Present' : 'Absent'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getRiskIcon(riskFactors.diabetes)}
                  <span>Diabetes</span>
                </div>
                <Badge variant={riskFactors.diabetes ? 'destructive' : 'secondary'}>
                  {riskFactors.diabetes ? 'Present' : 'Absent'}
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getRiskIcon(riskFactors.smoking)}
                  <Cigarette className="h-4 w-4" />
                  <span>Smoking</span>
                </div>
                <Badge variant={riskFactors.smoking ? 'destructive' : 'secondary'}>
                  {riskFactors.smoking ? 'Active' : 'Non-smoker'}
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getRiskIcon(riskFactors.familyHistory)}
                  <span>Family History</span>
                </div>
                <Badge variant={riskFactors.familyHistory ? 'destructive' : 'secondary'}>
                  {riskFactors.familyHistory ? 'Positive' : 'Negative'}
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getRiskIcon(riskFactors.sedentary)}
                  <Activity className="h-4 w-4" />
                  <span>Sedentary Lifestyle</span>
                </div>
                <Badge variant={riskFactors.sedentary ? 'destructive' : 'secondary'}>
                  {riskFactors.sedentary ? 'Yes' : 'No'}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="ascvd">
        <ASCVDRiskCalculator />
      </TabsContent>
    </Tabs>
  );
}