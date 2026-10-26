import { useState } from 'react'
import { deleteAccount, exportAccount } from '../services/account'

export function Account() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function downloadExport() {
    setError(null)
    try {
      const data = await exportAccount()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'learning-roadmap-account-export.json'
      anchor.click()
      URL.revokeObjectURL(url)
      setMessage('Your account export is ready.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to export account data') }
  }

  async function removeAccount() {
    setError(null)
    setMessage(null)
    try {
      await deleteAccount(email)
      localStorage.removeItem('access_token')
      window.location.assign('/login')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to delete account') }
  }

  return <main>
    <div className="eyebrow">Account and privacy</div>
    <h1>Account settings</h1>
    <p className="lede">Export your learning data or permanently remove your account.</p>
    <section className="panel" aria-labelledby="export-heading">
      <div className="panel-heading"><div><span className="section-kicker">Data portability</span><h2 id="export-heading">Download your data</h2></div></div>
      <p>Exports your profile, courses, concepts, progress, quiz attempts, roadmaps, resources, and mapping decisions as JSON.</p>
      <button className="primary" type="button" onClick={downloadExport}>Download export</button>
    </section>
    <section className="panel" aria-labelledby="delete-heading">
      <div className="panel-heading"><div><span className="section-kicker">Irreversible action</span><h2 id="delete-heading">Delete account</h2></div></div>
      <p>Enter your account email to confirm permanent deletion of your account and learning data.</p>
      <label htmlFor="confirm-email">Account email</label>
      <input id="confirm-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" />
      <button className="secondary" type="button" onClick={removeAccount} disabled={!email}>Delete account</button>
    </section>
    {message && <p role="status">{message}</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </main>
}
