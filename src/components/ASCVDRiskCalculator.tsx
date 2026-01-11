import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { Progress } from "./ui/progress";
import { Calculator, Heart, AlertTriangle, CheckCircle, Info } from "lucide-react";

interface ASCVDInputs {
  sex: 'male' | 'female' | '';
  age: number;
  race: 'white' | 'black' | 'other' | '';
  totalCholesterol: number;
  hdlCholesterol: number;
  systolicBP: number;
  onBPTreatment: boolean;
  diabetes: boolean;
  smoker: boolean;
}

interface ASCVDResult {
  riskPercent: number;
  percentile: number;
  riskCategory: 'low' | 'borderline' | 'intermediate' | 'high';
  statinRecommendation: string;
  lifestyle: string[];
  additionalConsiderations: string[];
}

export function ASCVDRiskCalculator() {
  const [inputs, setInputs] = useState<ASCVDInputs>({
    sex: '',
    age: 55,
    race: '',
    totalCholesterol: 200,
    hdlCholesterol: 50,
    systolicBP: 130,
    onBPTreatment: false,
    diabetes: false,
    smoker: false
  });

  const [result, setResult] = useState<ASCVDResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // ASCVD Risk Calculation Logic
  const calculateASCVDRisk = (inputs: ASCVDInputs): ASCVDResult => {
    const { sex, age, race, totalCholesterol, hdlCholesterol, systolicBP, onBPTreatment, diabetes, smoker } = inputs;
    
    // Pooled Cohort Risk Equations coefficients
    let coefficients: { [key: string]: number };
    let meanValues: { [key: string]: number };
    let baseSurvival: number;
    
    if (sex === 'male') {
      if (race === 'white') {
        coefficients = {
          lnAge: 12.344,
          lnTotalChol: 11.853,
          lnHDL: -2.664,
          lnAgeTotalChol: -2.580,
          lnAgeHDL: 0.0,
          lnTreatedSysBP: 1.797,
          lnUntreatedSysBP: 1.764,
          lnAgeTreatedSysBP: 0.0,
          lnAgeUntreatedSysBP: 0.0,
          smoker: 7.837,
          lnAgeSmoker: -1.795,
          diabetes: 0.658
        };
        meanValues = {
          lnAge: 3.6928,
          lnTotalChol: 5.3742,
          lnHDL: 3.8888,
          lnAgeTotalChol: 19.8444,
          lnAgeHDL: 14.3570,
          lnTreatedSysBP: 1.8446,
          lnUntreatedSysBP: 4.9415,
          lnAgeTreatedSysBP: 6.8144,
          lnAgeUntreatedSysBP: 18.2704,
          smoker: 0.3181,
          lnAgeSmoker: 1.1737,
          diabetes: 0.1058
        };
        baseSurvival = 0.9144;
      } else if (race === 'black') {
        coefficients = {
          lnAge: 2.469,
          lnTotalChol: 0.302,
          lnHDL: -0.307,
          lnAgeTotalChol: 0.0,
          lnAgeHDL: 0.0,
          lnTreatedSysBP: 1.809,
          lnUntreatedSysBP: 1.916,
          lnAgeTreatedSysBP: 0.0,
          lnAgeUntreatedSysBP: 0.0,
          smoker: 0.549,
          lnAgeSmoker: 0.0,
          diabetes: 0.645
        };
        meanValues = {
          lnAge: 3.8686,
          lnTotalChol: 5.4259,
          lnHDL: 3.8597,
          lnAgeTotalChol: 20.9776,
          lnAgeHDL: 14.9298,
          lnTreatedSysBP: 2.5185,
          lnUntreatedSysBP: 4.5297,
          lnAgeTreatedSysBP: 9.7528,
          lnAgeUntreatedSysBP: 17.5203,
          smoker: 0.4711,
          lnAgeSmoker: 1.8233,
          diabetes: 0.2078
        };
        baseSurvival = 0.8954;
      } else {
        // Use white male coefficients for other races
        coefficients = {
          lnAge: 12.344,
          lnTotalChol: 11.853,
          lnHDL: -2.664,
          lnAgeTotalChol: -2.580,
          lnAgeHDL: 0.0,
          lnTreatedSysBP: 1.797,
          lnUntreatedSysBP: 1.764,
          lnAgeTreatedSysBP: 0.0,
          lnAgeUntreatedSysBP: 0.0,
          smoker: 7.837,
          lnAgeSmoker: -1.795,
          diabetes: 0.658
        };
        meanValues = {
          lnAge: 3.6928,
          lnTotalChol: 5.3742,
          lnHDL: 3.8888,
          lnAgeTotalChol: 19.8444,
          lnAgeHDL: 14.3570,
          lnTreatedSysBP: 1.8446,
          lnUntreatedSysBP: 4.9415,
          lnAgeTreatedSysBP: 6.8144,
          lnAgeUntreatedSysBP: 18.2704,
          smoker: 0.3181,
          lnAgeSmoker: 1.1737,
          diabetes: 0.1058
        };
        baseSurvival = 0.9144;
      }
    } else {
      if (race === 'white') {
        coefficients = {
          lnAge: -29.799,
          lnTotalChol: 4.884,
          lnHDL: -13.540,
          lnAgeTotalChol: -3.114,
          lnAgeHDL: 3.149,
          lnTreatedSysBP: 2.019,
          lnUntreatedSysBP: 1.957,
          lnAgeTreatedSysBP: 0.0,
          lnAgeUntreatedSysBP: 0.0,
          smoker: 7.574,
          lnAgeSmoker: -1.665,
          diabetes: 0.661
        };
        meanValues = {
          lnAge: 3.7063,
          lnTotalChol: 5.3756,
          lnHDL: 4.0429,
          lnAgeTotalChol: 19.9265,
          lnAgeHDL: 14.9840,
          lnTreatedSysBP: 1.8074,
          lnUntreatedSysBP: 4.8842,
          lnAgeTreatedSysBP: 6.7025,
          lnAgeUntreatedSysBP: 18.1048,
          smoker: 0.2501,
          lnAgeSmoker: 0.9265,
          diabetes: 0.0404
        };
        baseSurvival = 0.9665;
      } else if (race === 'black') {
        coefficients = {
          lnAge: 17.114,
          lnTotalChol: 0.940,
          lnHDL: -18.920,
          lnAgeTotalChol: 0.0,
          lnAgeHDL: 4.475,
          lnTreatedSysBP: 29.291,
          lnUntreatedSysBP: 27.820,
          lnAgeTreatedSysBP: -6.432,
          lnAgeUntreatedSysBP: -6.087,
          smoker: 0.691,
          lnAgeSmoker: 0.0,
          diabetes: 0.874
        };
        meanValues = {
          lnAge: 3.8637,
          lnTotalChol: 5.4152,
          lnHDL: 4.0341,
          lnAgeTotalChol: 20.9261,
          lnAgeHDL: 15.5915,
          lnTreatedSysBP: 2.5288,
          lnUntreatedSysBP: 4.4623,
          lnAgeTreatedSysBP: 9.7759,
          lnAgeUntreatedSysBP: 17.2374,
          smoker: 0.2648,
          lnAgeSmoker: 1.0226,
          diabetes: 0.1156
        };
        baseSurvival = 0.9533;
      } else {
        // Use white female coefficients for other races
        coefficients = {
          lnAge: -29.799,
          lnTotalChol: 4.884,
          lnHDL: -13.540,
          lnAgeTotalChol: -3.114,
          lnAgeHDL: 3.149,
          lnTreatedSysBP: 2.019,
          lnUntreatedSysBP: 1.957,
          lnAgeTreatedSysBP: 0.0,
          lnAgeUntreatedSysBP: 0.0,
          smoker: 7.574,
          lnAgeSmoker: -1.665,
          diabetes: 0.661
        };
        meanValues = {
          lnAge: 3.7063,
          lnTotalChol: 5.3756,
          lnHDL: 4.0429,
          lnAgeTotalChol: 19.9265,
          lnAgeHDL: 14.9840,
          lnTreatedSysBP: 1.8074,
          lnUntreatedSysBP: 4.8842,
          lnAgeTreatedSysBP: 6.7025,
          lnAgeUntreatedSysBP: 18.1048,
          smoker: 0.2501,
          lnAgeSmoker: 0.9265,
          diabetes: 0.0404
        };
        baseSurvival = 0.9665;
      }
    }

    // Calculate natural log values
    const lnAge = Math.log(age);
    const lnTotalChol = Math.log(totalCholesterol);
    const lnHDL = Math.log(hdlCholesterol);
    const lnSysBP = Math.log(systolicBP);

    // Calculate individual sum
    let individualSum = 
      coefficients.lnAge * lnAge +
      coefficients.lnTotalChol * lnTotalChol +
      coefficients.lnHDL * lnHDL +
      coefficients.lnAgeTotalChol * lnAge * lnTotalChol +
      coefficients.lnAgeHDL * lnAge * lnHDL +
      (onBPTreatment ? coefficients.lnTreatedSysBP * lnSysBP : coefficients.lnUntreatedSysBP * lnSysBP) +
      (onBPTreatment ? coefficients.lnAgeTreatedSysBP * lnAge * lnSysBP : coefficients.lnAgeUntreatedSysBP * lnAge * lnSysBP) +
      (smoker ? coefficients.smoker : 0) +
      coefficients.lnAgeSmoker * lnAge * (smoker ? 1 : 0) +
      (diabetes ? coefficients.diabetes : 0);

    // Calculate mean sum
    let meanSum = 
      coefficients.lnAge * meanValues.lnAge +
      coefficients.lnTotalChol * meanValues.lnTotalChol +
      coefficients.lnHDL * meanValues.lnHDL +
      coefficients.lnAgeTotalChol * meanValues.lnAgeTotalChol +
      coefficients.lnAgeHDL * meanValues.lnAgeHDL +
      coefficients.lnTreatedSysBP * meanValues.lnTreatedSysBP +
      coefficients.lnUntreatedSysBP * meanValues.lnUntreatedSysBP +
      coefficients.lnAgeTreatedSysBP * meanValues.lnAgeTreatedSysBP +
      coefficients.lnAgeUntreatedSysBP * meanValues.lnAgeUntreatedSysBP +
      coefficients.smoker * meanValues.smoker +
      coefficients.lnAgeSmoker * meanValues.lnAgeSmoker +
      coefficients.diabetes * meanValues.diabetes;

    // Calculate risk
    const riskPercent = Math.max(0, Math.min(100, (1 - Math.pow(baseSurvival, Math.exp(individualSum - meanSum))) * 100));

    // Determine percentile (simplified approximation)
    let percentile = 50;
    if (riskPercent < 5) percentile = 25;
    else if (riskPercent < 7.5) percentile = 40;
    else if (riskPercent < 10) percentile = 60;
    else if (riskPercent < 20) percentile = 80;
    else percentile = 95;

    // Determine risk category
    let riskCategory: 'low' | 'borderline' | 'intermediate' | 'high';
    if (riskPercent < 5) riskCategory = 'low';
    else if (riskPercent < 7.5) riskCategory = 'borderline';
    else if (riskPercent < 20) riskCategory = 'intermediate';
    else riskCategory = 'high';

    // Statin recommendations based on 2018 AHA/ACC Guidelines
    let statinRecommendation = '';
    if (riskPercent >= 20) {
      statinRecommendation = 'High-intensity statin recommended (Class I recommendation)';
    } else if (riskPercent >= 7.5 && riskPercent < 20) {
      statinRecommendation = 'Moderate to high-intensity statin recommended. Consider risk enhancers and patient preferences (Class IIa recommendation)';
    } else if (riskPercent >= 5 && riskPercent < 7.5) {
      statinRecommendation = 'Consider moderate-intensity statin if risk enhancers present (Class IIb recommendation)';
    } else {
      statinRecommendation = 'Lifestyle modifications recommended. Statin generally not indicated unless risk enhancers present';
    }

    // Lifestyle recommendations
    const lifestyle = [
      'Mediterranean or DASH diet',
      'Regular physical activity (≥150 min/week moderate intensity)',
      'Weight management (BMI 18.5-24.9 kg/m²)',
      'Smoking cessation if applicable',
      'Limit alcohol consumption',
      'Stress management techniques'
    ];

    // Additional considerations
    const additionalConsiderations = [];
    if (age >= 65) additionalConsiderations.push('Consider aspirin for primary prevention if bleeding risk is low');
    if (riskPercent >= 7.5) additionalConsiderations.push('Consider risk enhancers: family history, chronic kidney disease, metabolic syndrome, inflammatory conditions');
    if (riskPercent >= 5) additionalConsiderations.push('May benefit from coronary artery calcium scoring for risk reclassification');
    if (onBPTreatment) additionalConsiderations.push('Optimize blood pressure control (target <130/80 mmHg)');
    if (diabetes) additionalConsiderations.push('Intensive diabetes management (HbA1c <7% for most patients)');

    return {
      riskPercent: Math.round(riskPercent * 10) / 10,
      percentile,
      riskCategory,
      statinRecommendation,
      lifestyle,
      additionalConsiderations
    };
  };

  const handleCalculate = () => {
    if (!inputs.sex || !inputs.race) return;
    
    setIsCalculating(true);
    setTimeout(() => {
      const calculatedResult = calculateASCVDRisk(inputs);
      setResult(calculatedResult);
      setIsCalculating(false);
    }, 500);
  };

  const isFormValid = inputs.sex && inputs.race && inputs.age >= 40 && inputs.age <= 79;

  const getRiskColor = (category: string) => {
    switch (category) {
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      case 'borderline': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'intermediate': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRiskIcon = (category: string) => {
    switch (category) {
      case 'low': return <CheckCircle className="h-4 w-4" />;
      case 'borderline': return <Info className="h-4 w-4" />;
      case 'intermediate': return <AlertTriangle className="h-4 w-4" />;
      case 'high': return <AlertTriangle className="h-4 w-4" />;
      default: return <Info className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Calculator className="h-5 w-5 text-primary" />
            <CardTitle>ASCVD 10-Year Risk Calculator</CardTitle>
          </div>
          <CardDescription>
            Pooled Cohort Equations to predict 10-year atherosclerotic cardiovascular disease risk
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="sex">Sex *</Label>
              <Select value={inputs.sex} onValueChange={(value: 'male' | 'female') => setInputs(prev => ({...prev, sex: value}))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select sex" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="male">Male</SelectItem>
                  <SelectItem value="female">Female</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="age">Age (40-79 years) *</Label>
              <Input
                id="age"
                type="number"
                min="40"
                max="79"
                value={inputs.age}
                onChange={(e) => setInputs(prev => ({...prev, age: parseInt(e.target.value) || 40}))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="race">Race *</Label>
              <Select value={inputs.race} onValueChange={(value: 'white' | 'black' | 'other') => setInputs(prev => ({...prev, race: value}))}>
                <SelectTrigger>
                  <SelectValue placeholder="Select race" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="white">White</SelectItem>
                  <SelectItem value="black">Black/African American</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="totalChol">Total Cholesterol (mg/dL)</Label>
              <Input
                id="totalChol"
                type="number"
                min="130"
                max="320"
                value={inputs.totalCholesterol}
                onChange={(e) => setInputs(prev => ({...prev, totalCholesterol: parseInt(e.target.value) || 200}))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="hdlChol">HDL Cholesterol (mg/dL)</Label>
              <Input
                id="hdlChol"
                type="number"
                min="20"
                max="100"
                value={inputs.hdlCholesterol}
                onChange={(e) => setInputs(prev => ({...prev, hdlCholesterol: parseInt(e.target.value) || 50}))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="sysBP">Systolic BP (mmHg)</Label>
              <Input
                id="sysBP"
                type="number"
                min="90"
                max="200"
                value={inputs.systolicBP}
                onChange={(e) => setInputs(prev => ({...prev, systolicBP: parseInt(e.target.value) || 130}))}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="bpTreatment"
                checked={inputs.onBPTreatment}
                onCheckedChange={(checked) => setInputs(prev => ({...prev, onBPTreatment: !!checked}))}
              />
              <Label htmlFor="bpTreatment">On blood pressure treatment</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="diabetes"
                checked={inputs.diabetes}
                onCheckedChange={(checked) => setInputs(prev => ({...prev, diabetes: !!checked}))}
              />
              <Label htmlFor="diabetes">Diabetes</Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="smoker"
                checked={inputs.smoker}
                onCheckedChange={(checked) => setInputs(prev => ({...prev, smoker: !!checked}))}
              />
              <Label htmlFor="smoker">Current smoker</Label>
            </div>
          </div>

          <div className="mt-6">
            <Button 
              onClick={handleCalculate} 
              disabled={!isFormValid || isCalculating}
              className="w-full md:w-auto"
            >
              {isCalculating ? 'Calculating...' : 'Calculate ASCVD Risk'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Heart className="h-5 w-5 text-red-500" />
                <CardTitle>Risk Assessment Results</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary mb-1">
                    {result.riskPercent}%
                  </div>
                  <p className="text-sm text-muted-foreground">10-Year ASCVD Risk</p>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-accent mb-1">
                    {result.percentile}th
                  </div>
                  <p className="text-sm text-muted-foreground">Percentile</p>
                </div>
                
                <div className="text-center">
                  <Badge className={`text-sm px-3 py-1 ${getRiskColor(result.riskCategory)}`}>
                    <div className="flex items-center space-x-1">
                      {getRiskIcon(result.riskCategory)}
                      <span className="capitalize">{result.riskCategory} Risk</span>
                    </div>
                  </Badge>
                </div>
              </div>

              <div className="mb-4">
                <Label className="text-sm">Risk Visualization</Label>
                <Progress value={Math.min(result.riskPercent, 30)} className="mt-2" />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0%</span>
                  <span>15%</span>
                  <span>30%+</span>
                </div>
              </div>

              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Statin Recommendation:</strong> {result.statinRecommendation}
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Lifestyle Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.lifestyle.map((item, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Additional Considerations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.additionalConsiderations.map((item, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm">{item}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}