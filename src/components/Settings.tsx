import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Switch } from "./ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { Separator } from "./ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { 
  User, 
  Bell, 
  Shield, 
  Palette, 
  Database, 
  Download, 
  Upload, 
  Key, 
  Globe, 
  Clock, 
  Mail, 
  Phone, 
  Building2, 
  UserCheck, 
  Settings as SettingsIcon,
  Save,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle2,
  Edit
} from "lucide-react";

interface UserProfile {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  role: string;
  department: string;
  institution: string;
  licenseNumber: string;
  specialization: string;
  avatar?: string;
  lastLogin: string;
  accountCreated: string;
  permissions: string[];
}

interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  dateFormat: string;
  notifications: {
    email: boolean;
    push: boolean;
    alerts: boolean;
    reports: boolean;
  };
  dataDisplay: {
    defaultView: string;
    itemsPerPage: number;
    showAdvancedMetrics: boolean;
    autoRefresh: boolean;
    refreshInterval: number;
  };
  privacy: {
    shareAnalytics: boolean;
    trackUsage: boolean;
    showOnlineStatus: boolean;
  };
}

export function Settings() {
  const [activeTab, setActiveTab] = useState("profile");
  const [showPassword, setShowPassword] = useState(false);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  // Mock user data
  const [userProfile, setUserProfile] = useState<UserProfile>({
    id: "USR001",
    firstName: "Dr. Sarah",
    lastName: "Mitchell",
    email: "s.mitchell@myfoundation.org",
    phone: "+1 (555) 123-4567",
    role: "Senior Cardiologist",
    department: "Cardiology Research",
    institution: "Magdi Yacoub Heart Foundation",
    licenseNumber: "MD-IL-12345",
    specialization: "Interventional Cardiology",
    lastLogin: "December 15, 2024 - 09:30 AM",
    accountCreated: "January 15, 2023",
    permissions: ["read", "write", "admin", "export", "analytics"]
  });

  const [appSettings, setAppSettings] = useState<AppSettings>({
    theme: 'light',
    language: 'en',
    timezone: 'America/Chicago',
    dateFormat: 'MM/DD/YYYY',
    notifications: {
      email: true,
      push: true,
      alerts: true,
      reports: false
    },
    dataDisplay: {
      defaultView: 'registry',
      itemsPerPage: 25,
      showAdvancedMetrics: true,
      autoRefresh: true,
      refreshInterval: 5
    },
    privacy: {
      shareAnalytics: false,
      trackUsage: true,
      showOnlineStatus: true
    }
  });

  const handleSaveProfile = () => {
    // Simulate API call
    setUnsavedChanges(false);
    // Show success message
  };

  const handleSaveSettings = () => {
    // Simulate API call
    setUnsavedChanges(false);
    // Show success message
  };

  const getRoleColor = (role: string) => {
    if (role.includes('Senior') || role.includes('Director')) return 'bg-primary text-primary-foreground';
    if (role.includes('Research')) return 'bg-accent text-accent-foreground';
    return 'bg-secondary text-secondary-foreground';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <SettingsIcon className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-2xl font-medium">Settings & Profile</h1>
            <p className="text-muted-foreground">Manage your account and application preferences</p>
          </div>
        </div>
        {unsavedChanges && (
          <Alert className="w-auto">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>You have unsaved changes</AlertDescription>
          </Alert>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile" className="flex items-center space-x-2">
            <User className="h-4 w-4" />
            <span>Profile</span>
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center space-x-2">
            <Palette className="h-4 w-4" />
            <span>Preferences</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center space-x-2">
            <Bell className="h-4 w-4" />
            <span>Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center space-x-2">
            <Shield className="h-4 w-4" />
            <span>Security</span>
          </TabsTrigger>
          <TabsTrigger value="data" className="flex items-center space-x-2">
            <Database className="h-4 w-4" />
            <span>Data & Privacy</span>
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Personal Information</CardTitle>
                  <CardDescription>Update your personal details and contact information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First Name</Label>
                      <Input
                        id="firstName"
                        value={userProfile.firstName}
                        onChange={(e) => {
                          setUserProfile(prev => ({...prev, firstName: e.target.value}));
                          setUnsavedChanges(true);
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last Name</Label>
                      <Input
                        id="lastName"
                        value={userProfile.lastName}
                        onChange={(e) => {
                          setUserProfile(prev => ({...prev, lastName: e.target.value}));
                          setUnsavedChanges(true);
                        }}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={userProfile.email}
                      onChange={(e) => {
                        setUserProfile(prev => ({...prev, email: e.target.value}));
                        setUnsavedChanges(true);
                      }}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                      id="phone"
                      value={userProfile.phone}
                      onChange={(e) => {
                        setUserProfile(prev => ({...prev, phone: e.target.value}));
                        setUnsavedChanges(true);
                      }}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="institution">Institution</Label>
                    <Input
                      id="institution"
                      value={userProfile.institution}
                      onChange={(e) => {
                        setUserProfile(prev => ({...prev, institution: e.target.value}));
                        setUnsavedChanges(true);
                      }}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="department">Department</Label>
                      <Input
                        id="department"
                        value={userProfile.department}
                        onChange={(e) => {
                          setUserProfile(prev => ({...prev, department: e.target.value}));
                          setUnsavedChanges(true);
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="role">Role</Label>
                      <Select 
                        value={userProfile.role} 
                        onValueChange={(value) => {
                          setUserProfile(prev => ({...prev, role: value}));
                          setUnsavedChanges(true);
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Senior Cardiologist">Senior Cardiologist</SelectItem>
                          <SelectItem value="Cardiologist">Cardiologist</SelectItem>
                          <SelectItem value="Research Fellow">Research Fellow</SelectItem>
                          <SelectItem value="Clinical Coordinator">Clinical Coordinator</SelectItem>
                          <SelectItem value="Data Analyst">Data Analyst</SelectItem>
                          <SelectItem value="Administrator">Administrator</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="license">License Number</Label>
                      <Input
                        id="license"
                        value={userProfile.licenseNumber}
                        onChange={(e) => {
                          setUserProfile(prev => ({...prev, licenseNumber: e.target.value}));
                          setUnsavedChanges(true);
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="specialization">Specialization</Label>
                      <Input
                        id="specialization"
                        value={userProfile.specialization}
                        onChange={(e) => {
                          setUserProfile(prev => ({...prev, specialization: e.target.value}));
                          setUnsavedChanges(true);
                        }}
                      />
                    </div>
                  </div>

                  <div className="flex justify-end pt-4">
                    <Button onClick={handleSaveProfile} disabled={!unsavedChanges}>
                      <Save className="h-4 w-4 mr-2" />
                      Save Profile
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Profile Overview</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <Avatar className="h-16 w-16">
                      <AvatarImage src={userProfile.avatar} />
                      <AvatarFallback className="text-lg">
                        {userProfile.firstName.charAt(0)}{userProfile.lastName.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="space-y-1">
                      <h3 className="font-medium">{userProfile.firstName} {userProfile.lastName}</h3>
                      <Badge className={getRoleColor(userProfile.role)}>
                        {userProfile.role}
                      </Badge>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-3 text-sm">
                    <div className="flex items-center space-x-2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <span>{userProfile.email}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Phone className="h-4 w-4 text-muted-foreground" />
                      <span>{userProfile.phone}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Building2 className="h-4 w-4 text-muted-foreground" />
                      <span>{userProfile.institution}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <UserCheck className="h-4 w-4 text-muted-foreground" />
                      <span>{userProfile.department}</span>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>Last login: {userProfile.lastLogin}</p>
                    <p>Member since: {userProfile.accountCreated}</p>
                  </div>

                  <Button variant="outline" size="sm" className="w-full">
                    <Edit className="h-4 w-4 mr-2" />
                    Change Avatar
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Permissions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {userProfile.permissions.map((permission) => (
                      <Badge key={permission} variant="outline" className="capitalize">
                        {permission}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Display Preferences</CardTitle>
                <CardDescription>Customize how data is displayed in the application</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="theme">Theme</Label>
                  <Select value={appSettings.theme} onValueChange={(value: 'light' | 'dark' | 'system') => {
                    setAppSettings(prev => ({...prev, theme: value}));
                    setUnsavedChanges(true);
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="dark">Dark</SelectItem>
                      <SelectItem value="system">System</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="defaultView">Default View</Label>
                  <Select value={appSettings.dataDisplay.defaultView} onValueChange={(value) => {
                    setAppSettings(prev => ({...prev, dataDisplay: {...prev.dataDisplay, defaultView: value}}));
                    setUnsavedChanges(true);
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="welcome">Welcome</SelectItem>
                      <SelectItem value="registry">Patient Registry</SelectItem>
                      <SelectItem value="analytics">Registry Analytics</SelectItem>
                      <SelectItem value="cohort">Cohort Builder</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="itemsPerPage">Items per Page</Label>
                  <Select value={appSettings.dataDisplay.itemsPerPage.toString()} onValueChange={(value) => {
                    setAppSettings(prev => ({...prev, dataDisplay: {...prev.dataDisplay, itemsPerPage: parseInt(value)}}));
                    setUnsavedChanges(true);
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10</SelectItem>
                      <SelectItem value="25">25</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Show Advanced Metrics</Label>
                    <p className="text-sm text-muted-foreground">Display detailed analytics and calculations</p>
                  </div>
                  <Switch
                    checked={appSettings.dataDisplay.showAdvancedMetrics}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, dataDisplay: {...prev.dataDisplay, showAdvancedMetrics: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Auto Refresh</Label>
                    <p className="text-sm text-muted-foreground">Automatically refresh data</p>
                  </div>
                  <Switch
                    checked={appSettings.dataDisplay.autoRefresh}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, dataDisplay: {...prev.dataDisplay, autoRefresh: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                {appSettings.dataDisplay.autoRefresh && (
                  <div className="space-y-2">
                    <Label htmlFor="refreshInterval">Refresh Interval (minutes)</Label>
                    <Select value={appSettings.dataDisplay.refreshInterval.toString()} onValueChange={(value) => {
                      setAppSettings(prev => ({...prev, dataDisplay: {...prev.dataDisplay, refreshInterval: parseInt(value)}}));
                      setUnsavedChanges(true);
                    }}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 minute</SelectItem>
                        <SelectItem value="5">5 minutes</SelectItem>
                        <SelectItem value="15">15 minutes</SelectItem>
                        <SelectItem value="30">30 minutes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveSettings} disabled={!unsavedChanges}>
                    <Save className="h-4 w-4 mr-2" />
                    Save Preferences
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Regional Settings</CardTitle>
                <CardDescription>Configure language, timezone, and format preferences</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select value={appSettings.language} onValueChange={(value) => {
                    setAppSettings(prev => ({...prev, language: value}));
                    setUnsavedChanges(true);
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="ar">Arabic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={appSettings.timezone} onValueChange={(value) => {
                    setAppSettings(prev => ({...prev, timezone: value}));
                    setUnsavedChanges(true);
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="America/New_York">Eastern Time</SelectItem>
                      <SelectItem value="America/Chicago">Central Time</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                      <SelectItem value="Europe/London">GMT</SelectItem>
                      <SelectItem value="Europe/Paris">Central European Time</SelectItem>
                      <SelectItem value="Asia/Dubai">Gulf Standard Time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="dateFormat">Date Format</Label>
                  <Select value={appSettings.dateFormat} onValueChange={(value) => {
                    setAppSettings(prev => ({...prev, dateFormat: value}));
                    setUnsavedChanges(true);
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                      <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                      <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                      <SelectItem value="DD MMM YYYY">DD MMM YYYY</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Globe className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Current Time Zone</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {new Intl.DateTimeFormat('en-US', {
                        timeZone: appSettings.timezone,
                        dateStyle: 'medium',
                        timeStyle: 'short'
                      }).format(new Date())}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">Sample Date</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {appSettings.dateFormat.replace('MM', '12').replace('DD', '31').replace('YYYY', '2024')}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>Control how and when you receive notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive notifications via email</p>
                  </div>
                  <Switch
                    checked={appSettings.notifications.email}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, notifications: {...prev.notifications, email: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Push Notifications</Label>
                    <p className="text-sm text-muted-foreground">Browser push notifications</p>
                  </div>
                  <Switch
                    checked={appSettings.notifications.push}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, notifications: {...prev.notifications, push: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Critical Alerts</Label>
                    <p className="text-sm text-muted-foreground">High-priority patient alerts and system notifications</p>
                  </div>
                  <Switch
                    checked={appSettings.notifications.alerts}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, notifications: {...prev.notifications, alerts: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Report Notifications</Label>
                    <p className="text-sm text-muted-foreground">Weekly and monthly analytics reports</p>
                  </div>
                  <Switch
                    checked={appSettings.notifications.reports}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, notifications: {...prev.notifications, reports: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">Notification Types</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-primary/10 rounded-full">
                          <AlertTriangle className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <h5 className="text-sm font-medium">Critical Alerts</h5>
                          <p className="text-xs text-muted-foreground">Patient emergencies, system failures</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-accent/10 rounded-full">
                          <CheckCircle2 className="h-4 w-4 text-accent" />
                        </div>
                        <div>
                          <h5 className="text-sm font-medium">System Updates</h5>
                          <p className="text-xs text-muted-foreground">Feature releases, maintenance</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSaveSettings} disabled={!unsavedChanges}>
                  <Save className="h-4 w-4 mr-2" />
                  Save Notification Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Password & Authentication</CardTitle>
                <CardDescription>Manage your password and authentication methods</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="currentPassword"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter current password"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <Input
                    id="newPassword"
                    type="password"
                    placeholder="Enter new password"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm new password"
                  />
                </div>

                <Alert>
                  <Key className="h-4 w-4" />
                  <AlertDescription>
                    Password must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters.
                  </AlertDescription>
                </Alert>

                <Button className="w-full">
                  <Key className="h-4 w-4 mr-2" />
                  Update Password
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Two-Factor Authentication</CardTitle>
                <CardDescription>Add an extra layer of security to your account</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-1">
                    <p className="font-medium">Authenticator App</p>
                    <p className="text-sm text-muted-foreground">Use an app like Google Authenticator</p>
                  </div>
                  <Badge variant="outline">Not Enabled</Badge>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-1">
                    <p className="font-medium">SMS Authentication</p>
                    <p className="text-sm text-muted-foreground">Receive codes via text message</p>
                  </div>
                  <Badge variant="outline">Not Enabled</Badge>
                </div>

                <Button variant="outline" className="w-full">
                  Set Up Two-Factor Authentication
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Data & Privacy Tab */}
        <TabsContent value="data">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Data Export & Import</CardTitle>
                <CardDescription>Manage your data portability and backups</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">Export Account Data</h4>
                        <p className="text-sm text-muted-foreground">Download all your account data</p>
                      </div>
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Export
                      </Button>
                    </div>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">Import Configuration</h4>
                        <p className="text-sm text-muted-foreground">Import settings from backup</p>
                      </div>
                      <Button variant="outline" size="sm">
                        <Upload className="h-4 w-4 mr-2" />
                        Import
                      </Button>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="font-medium">Data Retention</h4>
                  <p className="text-sm text-muted-foreground">
                    Your data is retained according to our privacy policy and regulatory requirements.
                    Patient data is stored securely and anonymized for research purposes.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Privacy Settings</CardTitle>
                <CardDescription>Control how your information is used</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Share Analytics</Label>
                    <p className="text-sm text-muted-foreground">Help improve the platform with usage analytics</p>
                  </div>
                  <Switch
                    checked={appSettings.privacy.shareAnalytics}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, privacy: {...prev.privacy, shareAnalytics: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Usage Tracking</Label>
                    <p className="text-sm text-muted-foreground">Track feature usage for optimization</p>
                  </div>
                  <Switch
                    checked={appSettings.privacy.trackUsage}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, privacy: {...prev.privacy, trackUsage: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Show Online Status</Label>
                    <p className="text-sm text-muted-foreground">Let others see when you're online</p>
                  </div>
                  <Switch
                    checked={appSettings.privacy.showOnlineStatus}
                    onCheckedChange={(checked) => {
                      setAppSettings(prev => ({...prev, privacy: {...prev.privacy, showOnlineStatus: checked}}));
                      setUnsavedChanges(true);
                    }}
                  />
                </div>

                <Separator />

                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    All patient data is encrypted and stored in compliance with HIPAA and GDPR regulations.
                    Your privacy and data security are our top priorities.
                  </AlertDescription>
                </Alert>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveSettings} disabled={!unsavedChanges}>
                    <Save className="h-4 w-4 mr-2" />
                    Save Privacy Settings
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}