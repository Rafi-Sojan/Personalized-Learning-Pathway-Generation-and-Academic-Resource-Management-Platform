import { FormEvent, useState } from 'react'
import { Compass, LockKeyhole } from 'lucide-react'
import { login } from '../services/auth'

export function Login({ onSuccess }: { onSuccess: () => void }) {
  const [email, setEmail] = useState('demo@example.com')
  const [password, setPassword] = useState('demo-password')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(null)
    try { await login(email, password); onSuccess() } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to sign in') } finally { setBusy(false) }
  }
  return <div className="login-shell"><form className="login-card" onSubmit={submit}><div className="login-brand"><div className="brand-mark"><Compass size={20} /></div><span>pathway<span className="brand-dot">.</span></span></div><span className="section-kicker">Your learning workspace</span><h1>Welcome back.</h1><p>Sign in to continue your personalized roadmap.</p><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} /></label>{error && <div className="form-error">{error}</div>}<button className="primary" disabled={busy}><LockKeyhole size={16} />{busy ? 'Signing in…' : 'Sign in'}</button><small>Development account: demo@example.com / demo-password</small></form></div>
}
