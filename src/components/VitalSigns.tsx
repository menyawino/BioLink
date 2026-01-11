import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Heart, Thermometer, Scale } from "lucide-react";

interface VitalSignsProps {
  vitals: {
    hasData?: boolean;
    current: {
      systolic: number;
      diastolic: number;
      heartRate: number;
      temperature: number | null;
      weight: number;
      cholesterol: {
        total: number | null;
        ldl: number | null;
        hdl: number | null;
      };
    };
    history: Array<{
      date: string;
      systolic: number;
      diastolic: number;
      heartRate: number;
    }>;
  };
}

export function VitalSigns({ vitals }: VitalSignsProps) {
  const getBPStatus = (systolic: number, diastolic: number) => {
    if (!systolic || !diastolic) return { status: 'Not recorded', variant: 'outline' as const };
    if (systolic >= 140 || diastolic >= 90) return { status: 'High', variant: 'destructive' as const };
    if (systolic >= 120 || diastolic >= 80) return { status: 'Elevated', variant: 'default' as const };
    return { status: 'Normal', variant: 'secondary' as const };
  };

  const getHRStatus = (hr: number) => {
    if (!hr) return { status: 'Not recorded', variant: 'outline' as const, icon: Activity };
    if (hr > 100) return { status: 'High', variant: 'destructive' as const, icon: TrendingUp };
    if (hr < 60) return { status: 'Low', variant: 'default' as const, icon: TrendingDown };
    return { status: 'Normal', variant: 'secondary' as const, icon: Activity };
  };

  const bpStatus = getBPStatus(vitals.current.systolic, vitals.current.diastolic);
  const hrStatus = getHRStatus(vitals.current.heartRate);

  const hasBloodPressure = vitals.current.systolic > 0 && vitals.current.diastolic > 0;
  const hasHeartRate = vitals.current.heartRate > 0;
  const hasWeight = vitals.current.weight > 0;
  const hasCholesterol = vitals.current.cholesterol.total !== null || 
                         vitals.current.cholesterol.ldl !== null || 
                         vitals.current.cholesterol.hdl !== null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">Blood Pressure</CardTitle>
            <Heart className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            {hasBloodPressure ? (
              <>
                <div className="text-2xl">{vitals.current.systolic}/{vitals.current.diastolic}</div>
                <p className="text-xs text-muted-foreground">mmHg</p>
                <Badge variant={bpStatus.variant} className="mt-2">
                  {bpStatus.status}
                </Badge>
              </>
            ) : (
              <p className="text-sm text-muted-foreground italic">Not recorded for this patient</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">Heart Rate</CardTitle>
            <hrStatus.icon className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            {hasHeartRate ? (
              <>
                <div className="text-2xl">{vitals.current.heartRate}</div>
                <p className="text-xs text-muted-foreground">bpm</p>
                <Badge variant={hrStatus.variant} className="mt-2">
                  {hrStatus.status}
                </Badge>
              </>
            ) : (
              <p className="text-sm text-muted-foreground italic">Not recorded for this patient</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">Weight</CardTitle>
            <Scale className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            {hasWeight ? (
              <>
                <div className="text-2xl">{vitals.current.weight} kg</div>
                <p className="text-xs text-muted-foreground">Body weight</p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground italic">Not recorded for this patient</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Blood Pressure Trend</CardTitle>
          </CardHeader>
          <CardContent>
            {vitals.history.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={vitals.history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="systolic" 
                    stroke="#ef4444" 
                    strokeWidth={2}
                    name="Systolic"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="diastolic" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    name="Diastolic"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[200px] flex items-center justify-center">
                <p className="text-sm text-muted-foreground italic">
                  Historical trend data not available. Only single measurement from enrollment.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cholesterol Levels</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {hasCholesterol ? (
              <>
                <div className="flex justify-between items-center">
                  <span>Total Cholesterol</span>
                  <div className="text-right">
                    {vitals.current.cholesterol.total !== null ? (
                      <>
                        <div>{vitals.current.cholesterol.total} mg/dL</div>
                        <Badge variant={vitals.current.cholesterol.total > 200 ? 'destructive' : 'secondary'}>
                          {vitals.current.cholesterol.total > 200 ? 'High' : 'Normal'}
                        </Badge>
                      </>
                    ) : (
                      <span className="text-muted-foreground italic">Not recorded</span>
                    )}
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span>LDL (Bad)</span>
                  <div className="text-right">
                    {vitals.current.cholesterol.ldl !== null ? (
                      <>
                        <div>{vitals.current.cholesterol.ldl} mg/dL</div>
                        <Badge variant={vitals.current.cholesterol.ldl > 100 ? 'destructive' : 'secondary'}>
                          {vitals.current.cholesterol.ldl > 100 ? 'High' : 'Normal'}
                        </Badge>
                      </>
                    ) : (
                      <span className="text-muted-foreground italic">Not recorded</span>
                    )}
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span>HDL (Good)</span>
                  <div className="text-right">
                    {vitals.current.cholesterol.hdl !== null ? (
                      <>
                        <div>{vitals.current.cholesterol.hdl} mg/dL</div>
                        <Badge variant={vitals.current.cholesterol.hdl < 40 ? 'destructive' : 'secondary'}>
                          {vitals.current.cholesterol.hdl < 40 ? 'Low' : 'Normal'}
                        </Badge>
                      </>
                    ) : (
                      <span className="text-muted-foreground italic">Not recorded</span>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="h-[100px] flex items-center justify-center">
                <p className="text-sm text-muted-foreground italic">
                  Cholesterol data not available in EHVol database.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}