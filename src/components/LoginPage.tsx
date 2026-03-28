/**
 * LoginPage - Full-screen login view for BioLink
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, LogIn, UserPlus, ArrowLeft, ShieldCheck, Database, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { registerApi } from '../api/auth';
import logo from "figma:asset/e26cb8b78ee049387f524876448562f480bca21b.png";

type Mode = 'login' | 'register';

export function LoginPage() {
  const { login } = useAuth();
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const resetForm = (clearSuccess = true) => {
    setUsername('');
    setPassword('');
    setEmail('');
    setFullName('');
    setConfirmPassword('');
    setError(null);
    if (clearSuccess) {
      setSuccess(null);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsSubmitting(true);
    try {
      await registerApi({ username, email, password, full_name: fullName || undefined });
      setSuccess('Account created successfully. You can now log in.');
      setMode('login');
      resetForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-shell min-h-screen bg-gradient-to-br from-background via-background to-muted/30 p-4 md:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] w-full max-w-6xl items-center gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="login-brand-panel hidden rounded-[2rem] border border-white/60 bg-white/72 p-8 shadow-[0_30px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:flex lg:flex-col lg:justify-between">
          <div className="space-y-8">
            <div className="space-y-4">
              <img src={logo} alt="Magdi Yacoub Heart Foundation" className="h-[4.5rem] w-auto" />
              <div className="space-y-3">
                <p className="section-kicker">Research platform</p>
                <h1 className="section-title max-w-xl">Move from registry search to evidence without losing context.</h1>
                <p className="section-subtitle max-w-xl">
                  BioLink brings cohort discovery, patient review, analytics, and AI-assisted exploration into one clinical workspace.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="metric-tile">
                <span className="metric-label">Secure access</span>
                <strong className="metric-value flex flex-col text-[1.15rem]"><ShieldCheck className="mb-2 h-5 w-5 text-primary" />Scoped roles</strong>
              </div>
              <div className="metric-tile">
                <span className="metric-label">Registry scale</span>
                <strong className="metric-value flex flex-col text-[1.15rem]"><Database className="mb-2 h-5 w-5 text-primary" />Live patient data</strong>
              </div>
              <div className="metric-tile">
                <span className="metric-label">Analysis flow</span>
                <strong className="metric-value flex flex-col text-[1.15rem]"><Activity className="mb-2 h-5 w-5 text-primary" />Research-ready views</strong>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-border/70 bg-background/70 p-5">
            <p className="text-sm font-semibold text-foreground">What you can do after sign-in</p>
            <div className="mt-3 grid gap-2 text-sm text-muted-foreground">
              <p>Search individual patient profiles and move through vitals, history, genomics, and imaging.</p>
              <p>Build cohorts and export focused subsets for downstream analysis.</p>
              <p>Use the BioLink Agent to move between questions, registry views, and analytics faster.</p>
            </div>
          </div>
        </div>

        <div className="w-full max-w-xl justify-self-center space-y-6 lg:w-full">
          <div className="text-center space-y-2 lg:hidden">
            <div className="flex justify-center">
              <img src={logo} alt="Magdi Yacoub Heart Foundation" className="h-16 w-auto" />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">MYF BioLink</h1>
            <p className="text-sm text-muted-foreground">
              Heart Foundation Patient Registry
            </p>
          </div>

          <Card className="login-card border-white/70 bg-white/86 shadow-[0_28px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl">
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-xl text-center">
                {mode === 'login' ? 'Sign In' : 'Create Account'}
              </CardTitle>
              <p className="text-center text-sm text-muted-foreground">
                {mode === 'login'
                  ? 'Continue to the BioLink research workspace.'
                  : 'Create a viewer account to access the registry experience.'}
              </p>
            </CardHeader>

            <CardContent>
              {error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              {success && (
                <Alert className="mb-4 border-green-500/50 text-green-700 dark:text-green-400">
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
              )}

              {mode === 'login' ? (
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input
                      id="username"
                      type="text"
                      autoComplete="username"
                      placeholder="Enter your username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      autoComplete="current-password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      disabled={isSubmitting}
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={isSubmitting}>
                    {isSubmitting ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <LogIn className="h-4 w-4 mr-2" />
                    )}
                    Sign In
                  </Button>
                  <div className="text-center">
                    <button
                      type="button"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                      onClick={() => { resetForm(); setMode('register'); }}
                    >
                      Don&apos;t have an account? <span className="underline">Sign up</span>
                    </button>
                  </div>
                </form>
              ) : (
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reg-fullname">Full Name</Label>
                    <Input
                      id="reg-fullname"
                      type="text"
                      autoComplete="name"
                      placeholder="Dr. Jane Smith"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-email">Email</Label>
                    <Input
                      id="reg-email"
                      type="email"
                      autoComplete="email"
                      placeholder="jane@institution.org"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-username">Username</Label>
                    <Input
                      id="reg-username"
                      type="text"
                      autoComplete="username"
                      placeholder="Choose a username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-password">Password</Label>
                    <Input
                      id="reg-password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="At least 8 characters"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      disabled={isSubmitting}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-confirm">Confirm Password</Label>
                    <Input
                      id="reg-confirm"
                      type="password"
                      autoComplete="new-password"
                      placeholder="Repeat your password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      disabled={isSubmitting}
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={isSubmitting}>
                    {isSubmitting ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <UserPlus className="h-4 w-4 mr-2" />
                    )}
                    Create Account
                  </Button>
                  <div className="text-center">
                    <button
                      type="button"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors inline-flex items-center gap-1"
                      onClick={() => { resetForm(); setMode('login'); }}
                    >
                      <ArrowLeft className="h-3 w-3" />
                      Back to sign in
                    </button>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>

          <p className="text-xs text-center text-muted-foreground">
            Magdi Yacoub Heart Foundation &middot; Cardiovascular Patient Registry
          </p>
        </div>
      </div>
    </div>
  );
}
