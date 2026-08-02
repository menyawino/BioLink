import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import {
  Loader2,
  Eye,
  EyeOff,
  User,
  Lock,
  Mail,
  UserCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { registerApi } from '../api/auth';
import logo from "figma:asset/e26cb8b78ee049387f524876448562f480bca21b.png";
import loginVisual from '../assets/login_visual.png';

type Mode = 'login' | 'request_access';

export function LoginPage() {
  const { login } = useAuth();
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
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
    if (clearSuccess) setSuccess(null);
  };

  const handleLogin = async (e: React.FormEvent | null, u = username, p = password) => {
    if (e) e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(u.trim().toLowerCase(), p);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickDemo = (role: string) => {
    setUsername(role);
    setPassword(role);
    handleLogin(null, role, role);
  };

  const handleRequestAccess = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) { setError('Passwords do not match'); return; }
    if (password.length < 8) { setError('Password must be at least 8 characters'); return; }
    setIsSubmitting(true);
    try {
      await registerApi({
        username: username.trim().toLowerCase(),
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim() || undefined,
      });
      setSuccess('Access request submitted. You can sign in once approved.');
      setMode('login');
      resetForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  /* shared input style token */
  const inputCls =
    'h-12 text-[15px] rounded-lg border border-slate-300 bg-white text-slate-900 ' +
    'placeholder:text-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ' +
    'transition-all shadow-sm';

  return (
    <div className="min-h-screen w-full flex font-sans">

      {/* ━━━ LEFT: Full-bleed photo ━━━ */}
      <div className="hidden lg:block lg:w-[55%] relative">
        {/* Photo — object-cover + center keeps the building centred at any viewport */}
        <img
          src={loginVisual}
          alt="Magdi Yacoub Heart Center, Aswan"
          className="absolute inset-0 w-full h-full object-cover object-center"
        />
        {/* Dark-to-transparent gradient from bottom so the text is legible */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />

        {/* Floating content pinned to bottom-left */}
        <div className="absolute bottom-0 left-0 right-0 p-10 xl:p-14 space-y-5">
          <div className="inline-flex items-center bg-white/95 backdrop-blur rounded-xl px-4 py-2.5 shadow-lg">
            <img src={logo} alt="MYF" className="h-9 w-auto object-contain" />
          </div>
          <h1 className="text-3xl xl:text-4xl font-extrabold text-white leading-snug drop-shadow-lg">
            BioLink Clinical<br />Data Platform
          </h1>
          <p className="text-base text-white/80 max-w-lg leading-relaxed drop-shadow">
            A secure environment for standardising, analysing, and exploring
            cardiovascular patient registries across multiple cohorts.
          </p>
          <div className="text-xs text-white/50 pt-2">
            © {new Date().getFullYear()} Magdi Yacoub Heart Foundation · v1.2.0
          </div>
        </div>
      </div>

      {/* ━━━ RIGHT: Form column ━━━ */}
      <div className="w-full lg:w-[45%] flex flex-col bg-white">
        {/* Mobile-only header */}
        <div className="lg:hidden flex items-center gap-3 p-6 border-b border-slate-100">
          <img src={logo} alt="MYF" className="h-8 w-auto object-contain" />
          <span className="text-base font-bold text-slate-800">BioLink</span>
        </div>

        {/* Vertically centred form area */}
        <div className="flex-1 flex items-center justify-center px-6 py-10 sm:px-12 lg:px-14 xl:px-20">
          <div className="w-full max-w-[420px] space-y-7">

            {/* Heading */}
            <div className="space-y-1">
              <h2 className="text-2xl font-bold text-slate-900">
                {mode === 'login' ? 'Welcome back' : 'Request Access'}
              </h2>
              <p className="text-sm text-slate-500">
                {mode === 'login'
                  ? 'Sign in to access the clinical workspace.'
                  : 'Fill in your details to request access.'}
              </p>
            </div>

            {/* Segmented control */}
            <div className="flex bg-slate-100 p-1 rounded-lg">
              {(['login', 'request_access'] as Mode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => { resetForm(); setMode(m); }}
                  className={`flex-1 py-2.5 text-sm font-semibold rounded-md transition-all ${
                    mode === m
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {m === 'login' ? 'Sign In' : 'Request Access'}
                </button>
              ))}
            </div>

            {/* Feedback */}
            {error && (
              <Alert variant="destructive" className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3">
                <AlertDescription className="text-sm">{error}</AlertDescription>
              </Alert>
            )}
            {success && (
              <Alert className="bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg px-4 py-3">
                <AlertDescription className="text-sm">{success}</AlertDescription>
              </Alert>
            )}

            {/* ── Sign In ── */}
            {mode === 'login' && (
              <form onSubmit={handleLogin} className="space-y-5">
                <div className="space-y-1.5">
                  <Label htmlFor="username" className="text-sm font-medium text-slate-700">
                    Username
                  </Label>
                  <div className="relative">
                    <User className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-slate-400" />
                    <Input
                      id="username"
                      type="text"
                      placeholder="Enter your username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className={`pl-10 ${inputCls}`}
                      required
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="password" className="text-sm font-medium text-slate-700">
                    Password
                  </Label>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-slate-400" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className={`pl-10 pr-11 ${inputCls}`}
                      required
                      disabled={isSubmitting}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff className="h-[18px] w-[18px]" /> : <Eye className="h-[18px] w-[18px]" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-12 text-[15px] font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-md shadow-blue-600/25 transition-all"
                >
                  {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Sign In
                </Button>

                {/* Quick demo row */}
                <div className="relative pt-5">
                  <div className="absolute inset-x-0 top-0 flex items-center" aria-hidden>
                    <div className="w-full border-t border-slate-200" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-white px-3 text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Demo accounts
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {(['admin', 'researcher', 'viewer'] as const).map((role) => (
                    <Button
                      key={role}
                      type="button"
                      variant="outline"
                      onClick={() => handleQuickDemo(role)}
                      className="h-10 text-sm font-medium rounded-lg border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 capitalize transition-all"
                    >
                      {role}
                    </Button>
                  ))}
                </div>
              </form>
            )}

            {/* ── Request Access ── */}
            {mode === 'request_access' && (
              <form onSubmit={handleRequestAccess} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="ra-name" className="text-sm font-medium text-slate-700">Full Name</Label>
                  <div className="relative">
                    <UserCheck className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-slate-400" />
                    <Input id="ra-name" placeholder="Dr. Jane Smith" value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className={`pl-10 ${inputCls}`} disabled={isSubmitting} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ra-email" className="text-sm font-medium text-slate-700">Institutional Email</Label>
                  <div className="relative">
                    <Mail className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-slate-400" />
                    <Input id="ra-email" type="email" placeholder="jane@institution.org" value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className={`pl-10 ${inputCls}`} required disabled={isSubmitting} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ra-user" className="text-sm font-medium text-slate-700">Desired Username</Label>
                  <div className="relative">
                    <User className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-slate-400" />
                    <Input id="ra-user" placeholder="Choose a username" value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className={`pl-10 ${inputCls}`} required disabled={isSubmitting} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ra-pass" className="text-sm font-medium text-slate-700">Password</Label>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-slate-400" />
                    <Input id="ra-pass" type="password" placeholder="At least 8 characters" value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className={`pl-10 ${inputCls}`} required disabled={isSubmitting} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="ra-conf" className="text-sm font-medium text-slate-700">Confirm Password</Label>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px] text-slate-400" />
                    <Input id="ra-conf" type="password" placeholder="Repeat your password" value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className={`pl-10 ${inputCls}`} required disabled={isSubmitting} />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full h-12 text-[15px] font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-md shadow-blue-600/25 transition-all mt-1"
                >
                  {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Submit Request
                </Button>
              </form>
            )}

          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 text-center text-xs text-slate-400 border-t border-slate-100">
          © {new Date().getFullYear()} Magdi Yacoub Heart Foundation
        </div>
      </div>
    </div>
  );
}
