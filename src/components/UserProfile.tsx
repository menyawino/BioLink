import { useEffect, useState } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Mail, Building2, Calendar, Shield, Award, Clock, FileText, Loader2, Check, Pencil, Lock } from "lucide-react";
import { useRegistryOverview } from "../hooks/useAnalytics";
import { useAuth } from "../context/AuthContext";
import {
  updateProfileApi,
  changePasswordApi,
  listUsersApi,
  adminUpdateUserApi,
  adminDeleteUserApi,
  adminCreateUserApi,
} from "../api/auth";
import type { AuthUser } from "../types/auth";

export function UserProfile() {
  const { user, refreshUser, hasRole } = useAuth();
  const { data: overview } = useRegistryOverview();
  const totalPatients = overview?.totalPatients?.toLocaleString() ?? '...';
  const isAdmin = hasRole('admin');

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

  // Admin user management state
  const [adminUsers, setAdminUsers] = useState<AuthUser[]>([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminSaving, setAdminSaving] = useState<Record<string, boolean>>({});
  const [adminMsg, setAdminMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [newUsername, setNewUsername] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [newRole, setNewRole] = useState<'admin' | 'researcher' | 'viewer'>('viewer');
  const [newScopes, setNewScopes] = useState<string[]>(['read']);
  const [newDisabled, setNewDisabled] = useState(false);
  const [newUserSaving, setNewUserSaving] = useState(false);

  const [userDrafts, setUserDrafts] = useState<Record<string, {
    role: string;
    scopes: string[];
    disabled: boolean;
    email: string;
    full_name: string;
  }>>({});

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

  const scopeKeys = ['read', 'write', 'delete', 'admin'];

  const loadAdminUsers = async () => {
    if (!isAdmin) return;
    setAdminLoading(true);
    setAdminMsg(null);
    try {
      const users = await listUsersApi();
      setAdminUsers(users);
      setUserDrafts(
        users.reduce((acc, u) => {
          acc[u.username] = {
            role: u.role,
            scopes: [...(u.scopes || [])],
            disabled: !!u.disabled,
            email: u.email || '',
            full_name: u.full_name || '',
          };
          return acc;
        }, {} as Record<string, {
          role: string;
          scopes: string[];
          disabled: boolean;
          email: string;
          full_name: string;
        }>)
      );
    } catch (err) {
      setAdminMsg({ type: 'error', text: err instanceof Error ? err.message : 'Failed to load users' });
    } finally {
      setAdminLoading(false);
    }
  };

  useEffect(() => {
    void loadAdminUsers();
  }, [isAdmin]);

  const toggleScope = (username: string, scope: string) => {
    setUserDrafts((prev) => {
      const draft = prev[username];
      if (!draft) return prev;
      const has = draft.scopes.includes(scope);
      return {
        ...prev,
        [username]: {
          ...draft,
          scopes: has ? draft.scopes.filter((s) => s !== scope) : [...draft.scopes, scope],
        },
      };
    });
  };

  const toggleNewScope = (scope: string) => {
    setNewScopes((prev) => (
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    ));
  };

  const applyRoleDefaults = (role: 'admin' | 'researcher' | 'viewer') => {
    setNewRole(role);
    if (role === 'admin') setNewScopes(['admin', 'read', 'write', 'delete']);
    if (role === 'researcher') setNewScopes(['read', 'write']);
    if (role === 'viewer') setNewScopes(['read']);
  };

  const saveManagedUser = async (username: string) => {
    const draft = userDrafts[username];
    if (!draft) return;

    setAdminSaving((prev) => ({ ...prev, [username]: true }));
    setAdminMsg(null);
    try {
      await adminUpdateUserApi(username, {
        role: draft.role,
        scopes: draft.scopes,
        disabled: draft.disabled,
        email: draft.email || undefined,
        full_name: draft.full_name || undefined,
      });
      await loadAdminUsers();
      setAdminMsg({ type: 'success', text: `Updated user '${username}'` });
    } catch (err) {
      setAdminMsg({ type: 'error', text: err instanceof Error ? err.message : 'Failed to update user' });
    } finally {
      setAdminSaving((prev) => ({ ...prev, [username]: false }));
    }
  };

  const deleteManagedUser = async (username: string) => {
    setAdminSaving((prev) => ({ ...prev, [username]: true }));
    setAdminMsg(null);
    try {
      await adminDeleteUserApi(username);
      await loadAdminUsers();
      setAdminMsg({ type: 'success', text: `Deleted user '${username}'` });
    } catch (err) {
      setAdminMsg({ type: 'error', text: err instanceof Error ? err.message : 'Failed to delete user' });
    } finally {
      setAdminSaving((prev) => ({ ...prev, [username]: false }));
    }
  };

  const createManagedUser = async () => {
    if (!newUsername.trim() || !newEmail.trim() || !newUserPassword.trim()) {
      setAdminMsg({ type: 'error', text: 'Username, email, and password are required' });
      return;
    }

    setNewUserSaving(true);
    setAdminMsg(null);
    try {
      await adminCreateUserApi({
        username: newUsername.trim().toLowerCase(),
        email: newEmail.trim().toLowerCase(),
        password: newUserPassword,
        full_name: newFullName.trim() || undefined,
        role: newRole,
        scopes: newScopes,
        disabled: newDisabled,
      });
      setNewUsername('');
      setNewEmail('');
      setNewFullName('');
      setNewUserPassword('');
      setNewDisabled(false);
      applyRoleDefaults('viewer');
      await loadAdminUsers();
      setAdminMsg({ type: 'success', text: 'User created successfully' });
    } catch (err) {
      setAdminMsg({ type: 'error', text: err instanceof Error ? err.message : 'Failed to create user' });
    } finally {
      setNewUserSaving(false);
    }
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

      {isAdmin && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5" style={{ color: '#00a2ddff' }} />
              <h3 className="text-lg font-semibold">Admin User Management</h3>
            </div>
            <Button size="sm" variant="outline" onClick={() => { void loadAdminUsers(); }} disabled={adminLoading}>
              {adminLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
            </Button>
          </div>

          {adminMsg && (
            <Alert variant={adminMsg.type === 'error' ? 'destructive' : 'default'} className={`mb-4 ${adminMsg.type === 'success' ? 'border-green-500/50 text-green-700 dark:text-green-400' : ''}`}>
              <AlertDescription>{adminMsg.text}</AlertDescription>
            </Alert>
          )}

          <div className="border rounded-lg p-4 mb-4 space-y-3">
            <p className="text-sm font-medium">Create New User</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Username</Label>
                <Input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} placeholder="username" />
              </div>
              <div className="space-y-1">
                <Label>Email</Label>
                <Input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder="user@example.org" />
              </div>
              <div className="space-y-1">
                <Label>Full Name</Label>
                <Input value={newFullName} onChange={(e) => setNewFullName(e.target.value)} placeholder="Optional" />
              </div>
              <div className="space-y-1">
                <Label>Temporary Password</Label>
                <Input type="password" value={newUserPassword} onChange={(e) => setNewUserPassword(e.target.value)} placeholder="At least 8 characters" />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Role</Label>
              <div className="flex flex-wrap gap-2">
                {(['viewer', 'researcher', 'admin'] as const).map((role) => (
                  <Button
                    key={role}
                    type="button"
                    size="sm"
                    variant={newRole === role ? 'default' : 'outline'}
                    onClick={() => applyRoleDefaults(role)}
                    className="capitalize"
                  >
                    {role}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Authorities (Scopes)</Label>
              <div className="flex flex-wrap gap-2">
                {scopeKeys.map((scope) => (
                  <Button
                    key={scope}
                    type="button"
                    size="sm"
                    variant={newScopes.includes(scope) ? 'default' : 'outline'}
                    onClick={() => toggleNewScope(scope)}
                    className="capitalize"
                  >
                    {scope}
                  </Button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between gap-3">
              <Button type="button" variant={newDisabled ? 'destructive' : 'outline'} size="sm" onClick={() => setNewDisabled((v) => !v)}>
                {newDisabled ? 'Will be created disabled' : 'Create as active'}
              </Button>
              <Button type="button" size="sm" onClick={createManagedUser} disabled={newUserSaving}>
                {newUserSaving ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : null}
                Create User
              </Button>
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium">Existing Users ({adminUsers.length})</p>
            {adminUsers.map((managedUser) => {
              const draft = userDrafts[managedUser.username];
              if (!draft) return null;
              const isSelf = managedUser.username === user?.username;

              return (
                <div key={managedUser.username} className="border rounded-lg p-4 space-y-3">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                    <div>
                      <p className="font-medium">{managedUser.username}</p>
                      <p className="text-sm text-muted-foreground">{managedUser.email || 'No email'} · {managedUser.full_name || 'No full name'}</p>
                    </div>
                    <Badge variant={draft.disabled ? 'destructive' : 'outline'}>{draft.disabled ? 'Disabled' : 'Active'}</Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label>Email</Label>
                      <Input value={draft.email} onChange={(e) => setUserDrafts((prev) => ({ ...prev, [managedUser.username]: { ...prev[managedUser.username], email: e.target.value } }))} />
                    </div>
                    <div className="space-y-1">
                      <Label>Full Name</Label>
                      <Input value={draft.full_name} onChange={(e) => setUserDrafts((prev) => ({ ...prev, [managedUser.username]: { ...prev[managedUser.username], full_name: e.target.value } }))} />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Role</Label>
                    <div className="flex flex-wrap gap-2">
                      {(['viewer', 'researcher', 'admin'] as const).map((role) => (
                        <Button
                          key={role}
                          type="button"
                          size="sm"
                          variant={draft.role === role ? 'default' : 'outline'}
                          onClick={() => setUserDrafts((prev) => ({ ...prev, [managedUser.username]: { ...prev[managedUser.username], role } }))}
                          className="capitalize"
                        >
                          {role}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Authorities (Scopes)</Label>
                    <div className="flex flex-wrap gap-2">
                      {scopeKeys.map((scope) => (
                        <Button
                          key={scope}
                          type="button"
                          size="sm"
                          variant={draft.scopes.includes(scope) ? 'default' : 'outline'}
                          onClick={() => toggleScope(managedUser.username, scope)}
                          className="capitalize"
                        >
                          {scope}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant={draft.disabled ? 'outline' : 'destructive'}
                      onClick={() => setUserDrafts((prev) => ({
                        ...prev,
                        [managedUser.username]: { ...prev[managedUser.username], disabled: !prev[managedUser.username].disabled },
                      }))}
                      disabled={isSelf}
                    >
                      {draft.disabled ? 'Re-enable Access' : 'Revoke Access'}
                    </Button>
                    <Button type="button" size="sm" onClick={() => { void saveManagedUser(managedUser.username); }} disabled={!!adminSaving[managedUser.username]}>
                      {adminSaving[managedUser.username] ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : null}
                      Save Changes
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => { void deleteManagedUser(managedUser.username); }}
                      disabled={isSelf || !!adminSaving[managedUser.username]}
                    >
                      Delete User
                    </Button>
                    {isSelf ? <span className="text-xs text-muted-foreground">Current account cannot be revoked/deleted.</span> : null}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

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
