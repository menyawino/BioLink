import { useState } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Mail, Building2, Calendar, Shield, Award, Clock, FileText, Loader2, Check, Pencil, Lock } from "lucide-react";
import { useRegistryOverview } from "../hooks/useAnalytics";
import { useAuth } from "../context/AuthContext";
import { updateProfileApi, changePasswordApi } from "../api/auth";

export function UserProfile() {
  const { user, refreshUser, hasRole } = useAuth();
  const { data: overview } = useRegistryOverview();
  const totalPatients = overview?.totalPatients?.toLocaleString() ?? '...';

  // Edit profile state
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editFullName, setEditFullName] = useState(user?.full_name || '');
  const [editEmail, setEditEmail] = useState(user?.email || '');
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Change password state
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.username?.slice(0, 2).toUpperCase() ?? '??';

  const roleBadgeColor = user?.role === 'admin'
    ? { backgroundColor: '#e9322b', color: 'white' }
    : user?.role === 'researcher'
    ? { backgroundColor: '#00a2ddff', color: 'white' }
    : {};

  const handleSaveProfile = async () => {
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      await updateProfileApi({
        full_name: editFullName || undefined,
        email: editEmail || undefined,
      });
      await refreshUser();
      setIsEditingProfile(false);
      setProfileMsg({ type: 'success', text: 'Profile updated successfully' });
    } catch (err) {
      setProfileMsg({ type: 'error', text: err instanceof Error ? err.message : 'Update failed' });
    } finally {
      setProfileSaving(false);
    }
  };

  const handleChangePassword = async () => {
    setPasswordMsg(null);
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'Passwords do not match' });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMsg({ type: 'error', text: 'Password must be at least 8 characters' });
      return;
    }
    setPasswordSaving(true);
    try {
      await changePasswordApi({ current_password: currentPassword, new_password: newPassword });
      setIsChangingPassword(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordMsg({ type: 'success', text: 'Password changed successfully' });
    } catch (err) {
      setPasswordMsg({ type: 'error', text: err instanceof Error ? err.message : 'Password change failed' });
    } finally {
      setPasswordSaving(false);
    }
  };

  const scopeLabels: Record<string, string> = {
    admin: 'System Administration',
    read: 'Patient Data Access',
    write: 'Data Modification',
    delete: 'Data Deletion',
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold mb-1">User Profile</h1>
        <p className="text-muted-foreground">Your account information and access details</p>
      </div>

      {profileMsg && (
        <Alert variant={profileMsg.type === 'error' ? 'destructive' : 'default'} className={profileMsg.type === 'success' ? 'border-green-500/50 text-green-700 dark:text-green-400' : ''}>
          <AlertDescription>{profileMsg.text}</AlertDescription>
        </Alert>
      )}

      {/* Profile Header Card */}
      <Card className="p-6">
        <div className="flex items-start space-x-6">
          <div className="h-24 w-24 rounded-full bg-gradient-to-br from-[#00a2ddff] to-[#efb01bff] flex items-center justify-center text-white text-3xl font-medium flex-shrink-0">
            {initials}
          </div>
          <div className="flex-1">
            {isEditingProfile ? (
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label>Full Name</Label>
                  <Input value={editFullName} onChange={e => setEditFullName(e.target.value)} placeholder="Full name" />
                </div>
                <div className="space-y-1">
                  <Label>Email</Label>
                  <Input value={editEmail} onChange={e => setEditEmail(e.target.value)} placeholder="Email" type="email" />
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleSaveProfile} disabled={profileSaving}>
                    {profileSaving ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Check className="h-4 w-4 mr-1" />}
                    Save
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setIsEditingProfile(false)}>Cancel</Button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-2xl font-semibold">{user?.full_name || user?.username}</h2>
                  <Button size="sm" variant="ghost" onClick={() => {
                    setEditFullName(user?.full_name || '');
                    setEditEmail(user?.email || '');
                    setIsEditingProfile(true);
                  }}>
                    <Pencil className="h-3 w-3" />
                  </Button>
                </div>
                <p className="text-muted-foreground mb-4">@{user?.username}</p>
                
                <div className="flex items-center space-x-2 mb-4">
                  <Badge className="px-3 py-1 capitalize" style={roleBadgeColor}>
                    {user?.role}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center space-x-2 text-sm">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>{user?.email || 'No email set'}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <span>Magdi Yacoub Heart Foundation</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>{user?.created_at ? `Member since ${new Date(user.created_at).toLocaleDateString()}` : 'Member'}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{user?.last_login ? `Last login: ${new Date(user.last_login).toLocaleString()}` : 'First login'}</span>
                  </div>
                </div>
              </>
            )}
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
                <span className="text-sm font-medium">Role</span>
                <Badge className="capitalize" style={roleBadgeColor}>{user?.role}</Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                {user?.role === 'admin' ? 'Full system access with administrative privileges' :
                 user?.role === 'researcher' ? 'Read and write access to patient data' :
                 'Read-only access to patient data'}
              </p>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Status</span>
                <Badge variant={user?.disabled ? 'destructive' : 'outline'}>
                  {user?.disabled ? 'Disabled' : 'Active'}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">Account status</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Granted Scopes */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Award className="h-5 w-5" style={{ color: '#efb01bff' }} />
          <h3 className="text-lg font-semibold">Granted Permissions</h3>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(scopeLabels).map(([scope, label]) => {
            const granted = user?.scopes?.includes(scope) ?? false;
            return (
              <div
                key={scope}
                className="p-3 border rounded-lg flex items-center justify-between"
              >
                <span className="text-sm">{label}</span>
                <div className={`h-2 w-2 rounded-full ${granted ? 'bg-green-500' : 'bg-gray-300'}`} />
              </div>
            );
          })}
        </div>
      </Card>

      {/* Change Password */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Lock className="h-5 w-5" style={{ color: '#00a2ddff' }} />
          <h3 className="text-lg font-semibold">Security</h3>
        </div>

        {passwordMsg && (
          <Alert variant={passwordMsg.type === 'error' ? 'destructive' : 'default'} className={`mb-4 ${passwordMsg.type === 'success' ? 'border-green-500/50 text-green-700 dark:text-green-400' : ''}`}>
            <AlertDescription>{passwordMsg.text}</AlertDescription>
          </Alert>
        )}

        {isChangingPassword ? (
          <div className="space-y-3 max-w-md">
            <div className="space-y-1">
              <Label>Current Password</Label>
              <Input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>New Password</Label>
              <Input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="At least 8 characters" />
            </div>
            <div className="space-y-1">
              <Label>Confirm New Password</Label>
              <Input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleChangePassword} disabled={passwordSaving}>
                {passwordSaving ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Check className="h-4 w-4 mr-1" />}
                Change Password
              </Button>
              <Button size="sm" variant="outline" onClick={() => {
                setIsChangingPassword(false);
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
                setPasswordMsg(null);
              }}>Cancel</Button>
            </div>
          </div>
        ) : (
          <Button variant="outline" onClick={() => setIsChangingPassword(true)}>
            <Lock className="h-4 w-4 mr-2" />
            Change Password
          </Button>
        )}
      </Card>

      {/* Activity Summary */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-4">
          <FileText className="h-5 w-5" style={{ color: '#00a2ddff' }} />
          <h3 className="text-lg font-semibold">Registry Summary</h3>
        </div>
        
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 border rounded-lg">
            <p className="text-2xl font-semibold mb-1" style={{ color: '#00a2ddff' }}>{totalPatients}</p>
            <p className="text-xs text-muted-foreground">Total Patients</p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-2xl font-semibold mb-1" style={{ color: '#efb01bff' }}>{user?.scopes?.length ?? 0}</p>
            <p className="text-xs text-muted-foreground">Active Scopes</p>
          </div>
          <div className="p-4 border rounded-lg">
            <p className="text-2xl font-semibold mb-1 capitalize" style={{ color: '#00a2ddff' }}>{user?.role}</p>
            <p className="text-xs text-muted-foreground">Current Role</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
