import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Mail, Phone, Building2, Calendar, Shield, Award, Clock, FileText } from "lucide-react";
import { useRegistryOverview } from "../hooks/useAnalytics";

export function UserProfile() {
  // Fetch real patient count from API
  const { data: overview } = useRegistryOverview();
  const totalPatients = overview?.totalPatients?.toLocaleString() ?? '...';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold mb-1">User Profile</h1>
        <p className="text-muted-foreground">Your account information and access details</p>
      </div>

      {/* Profile Header Card */}
      <Card className="p-6">
        <div className="flex items-start space-x-6">
          <div className="h-24 w-24 rounded-full bg-gradient-to-br from-[#00a2ddff] to-[#efb01bff] flex items-center justify-center text-white text-3xl font-medium flex-shrink-0">
            DR
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-semibold mb-1">Dr. Ahmed Hassan</h2>
            <p className="text-muted-foreground mb-4">Research Assistant</p>
            
            <div className="flex items-center space-x-2 mb-4">
              <Badge className="px-3 py-1" style={{ backgroundColor: '#e9322b', color: 'white' }}>
                Super Admin
              </Badge>
              <Badge variant="outline" className="px-3 py-1">
                Owner
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2 text-sm">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span>ahmed.hassan@myf.org.eg</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span>+20 123 456 7890</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <span>Magdi Yacoub Heart Foundation</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span>Member since Jan 2023</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Access & Permissions */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Shield className="h-5 w-5" style={{ color: '#00a2ddff' }} />
          <h3 className="text-lg font-semibold">Access & Permissions</h3>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Authority Tier</span>
                <Badge style={{ backgroundColor: '#e9322b', color: 'white' }}>Super Admin</Badge>
              </div>
              <p className="text-xs text-muted-foreground">Full system access with administrative privileges</p>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Role</span>
                <Badge variant="outline">Owner</Badge>
              </div>
              <p className="text-xs text-muted-foreground">System owner with all permissions</p>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Affiliation</span>
                <Badge variant="secondary">MYF</Badge>
              </div>
              <p className="text-xs text-muted-foreground">Magdi Yacoub Heart Foundation</p>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Department</span>
                <Badge variant="secondary">Research</Badge>
              </div>
              <p className="text-xs text-muted-foreground">Clinical Research & Registry Management</p>
            </div>
          </div>
        </div>
      </Card>

      {/* System Permissions */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Award className="h-5 w-5" style={{ color: '#efb01bff' }} />
          <h3 className="text-lg font-semibold">System Permissions</h3>
        </div>
        
        <div className="grid grid-cols-3 gap-3">
          {[
            { name: 'Patient Data Access', granted: true },
            { name: 'Registry Management', granted: true },
            { name: 'Cohort Builder', granted: true },
            { name: 'Data Export', granted: true },
            { name: 'Analytics & Reports', granted: true },
            { name: 'User Management', granted: true },
            { name: 'System Settings', granted: true },
            { name: 'Data Dictionary Edit', granted: true },
            { name: 'API Access', granted: true },
          ].map((permission) => (
            <div 
              key={permission.name}
              className="p-3 border rounded-lg flex items-center justify-between"
            >
              <span className="text-sm">{permission.name}</span>
              <div className={`h-2 w-2 rounded-full ${permission.granted ? 'bg-green-500' : 'bg-gray-300'}`} />
            </div>
          ))}
        </div>
      </Card>

      {/* Activity Summary */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Clock className="h-5 w-5" style={{ color: '#00a2ddff' }} />
          <h3 className="text-lg font-semibold">Activity Summary</h3>
        </div>
        
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 border rounded-lg">
            <p className="text-2xl font-semibold mb-1" style={{ color: '#00a2ddff' }}>{totalPatients}</p>
            <p className="text-xs text-muted-foreground">Patients Reviewed</p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-2xl font-semibold mb-1" style={{ color: '#efb01bff' }}>83</p>
            <p className="text-xs text-muted-foreground">Cohorts Created</p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-2xl font-semibold mb-1" style={{ color: '#00a2ddff' }}>456</p>
            <p className="text-xs text-muted-foreground">Reports Generated</p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-2xl font-semibold mb-1" style={{ color: '#efb01bff' }}>127</p>
            <p className="text-xs text-muted-foreground">Data Exports</p>
          </div>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <FileText className="h-5 w-5" style={{ color: '#00a2ddff' }} />
          <h3 className="text-lg font-semibold">Recent Activity</h3>
        </div>
        
        <div className="space-y-3">
          {[
            { action: 'Created cohort "High-Risk CAD Patients"', time: '2 hours ago', type: 'cohort' },
            { action: 'Exported patient registry data (CSV)', time: '5 hours ago', type: 'export' },
            { action: 'Updated patient MYF-001247 vitals', time: '1 day ago', type: 'update' },
            { action: 'Generated analytics report for Q4 2024', time: '2 days ago', type: 'report' },
            { action: 'Added new data dictionary entries', time: '3 days ago', type: 'dictionary' },
          ].map((activity, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
              <div className={`h-2 w-2 rounded-full mt-2 flex-shrink-0 ${
                activity.type === 'cohort' ? 'bg-[#00a2ddff]' :
                activity.type === 'export' ? 'bg-[#efb01bff]' :
                activity.type === 'update' ? 'bg-green-500' :
                activity.type === 'report' ? 'bg-[#00a2ddff]' :
                'bg-gray-400'
              }`} />
              <div className="flex-1">
                <p className="text-sm">{activity.action}</p>
                <p className="text-xs text-muted-foreground">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
