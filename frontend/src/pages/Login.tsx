import { FormEvent, useState } from 'react'
import { Compass, LockKeyhole } from 'lucide-react'
import { login, register } from '../services/auth'

/** Authenticate the learner and report successful login to the application shell. */
export function Login({ onSuccess }: { onSuccess: () => void }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [creatingAccount, setCreatingAccount] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  /** Submit credentials and expose authentication failures without losing form state. */
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(null)
    try {
      if (creatingAccount) await register(name, email, password)
      else await login(email, password)
      onSuccess()
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to authenticate') } finally { setBusy(false) }
  }
  return <div className="login-shell"><form className="login-card" onSubmit={submit}><div className="login-brand"><div className="brand-mark"><Compass size={20} /></div><span>pathway<span className="brand-dot">.</span></span></div><span className="section-kicker">RVCE learning workspace</span><h1>{creatingAccount ? 'Create account.' : 'Welcome back.'}</h1><p>{creatingAccount ? 'Create a learner account to map your syllabus.' : 'Sign in to continue your syllabus and study roadmap.'}</p>{creatingAccount && <label>Name<input type="text" value={name} onChange={(event) => setName(event.target.value)} minLength={2} maxLength={120} autoComplete="name" required /></label>}<label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={creatingAccount ? 'new-password' : 'current-password'} required minLength={8} /></label>{error && <div className="form-error">{error}</div>}<button className="primary" disabled={busy}><LockKeyhole size={16} />{busy ? 'Please wait…' : creatingAccount ? 'Create account' : 'Sign in'}</button><button className="secondary" type="button" onClick={() => { setCreatingAccount(!creatingAccount); setError(null) }}>{creatingAccount ? 'Already have an account? Sign in' : 'New learner? Create an account'}</button></form></div>
}
