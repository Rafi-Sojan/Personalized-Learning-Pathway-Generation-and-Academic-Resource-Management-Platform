import { useCallback, useMemo, useState, type FormEvent } from 'react'
import { useAsync } from '../hooks/useAsync'
import { enrollRvceSemester, getRvceCatalog } from '../services/rvce'

/** Let learners select a catalogued RVCE scheme and enroll verified semester courses. */
export function RvceCatalog() {
  const { data, loading, error } = useAsync(useCallback(() => getRvceCatalog(), []), [])
  const [program, setProgram] = useState('AS')
  const [scheme, setScheme] = useState(2025)
  const [semester, setSemester] = useState(3)
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const activeProgram = useMemo(() => data?.program_schemes.find((item) => item.code === program), [data, program])
  const schemes = semester <= 2 ? data?.common_first_year_schemes ?? [] : activeProgram?.schemes ?? []

  /** Enroll the chosen program, scheme, and semester through the authenticated API. */
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setMessage('')
    try {
      const result = await enrollRvceSemester({ program_code: program, scheme_year: scheme, semester })
      setMessage(`${result.created} course(s) added; ${result.existing} already in your library.`)
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : 'Could not add this semester.')
    } finally {
      setBusy(false)
    }
  }

  return <main><div className="eyebrow">RVCE syllabus</div><h1>Build your semester</h1><p className="lede">Choose your program and scheme. Only academically verified syllabus records can be added to your courses and roadmap.</p>
    {loading && <p aria-live="polite">Loading RVCE program catalog…</p>}
    {error && <p className="form-error" role="alert">Unable to load the RVCE catalog.</p>}
    {data && <section className="panel roadmap-controls"><form onSubmit={submit}>
      <div className="form-grid">
        <label>Program<select value={program} onChange={(event) => { setProgram(event.target.value); const next = data.program_schemes.find((entry) => entry.code === event.target.value); if (semester > 2 && next?.schemes.length) setScheme(next.schemes[next.schemes.length - 1]) }}>{data.program_schemes.map((entry) => <option key={entry.code} value={entry.code}>{entry.name} ({entry.code})</option>)}</select></label>
        <label>Semester<select value={semester} onChange={(event) => { const next = Number(event.target.value); setSemester(next); const options = next <= 2 ? data.common_first_year_schemes : activeProgram?.schemes ?? []; if (!options.includes(scheme) && options.length) setScheme(options[options.length - 1]) }}>{[1, 2, 3, 4, 5, 6, 7, 8].map((value) => <option key={value} value={value}>Semester {value}</option>)}</select></label>
        <label>Scheme<select value={scheme} onChange={(event) => setScheme(Number(event.target.value))}>{schemes.map((value) => <option key={value} value={value}>{value} scheme</option>)}</select></label>
      </div>
      <button className="primary" type="submit" disabled={busy || schemes.length === 0}>{busy ? 'Adding…' : 'Add verified semester courses'}</button>
      {message && <p aria-live="polite" className="mapping-status">{message}</p>}
      <p className="mapping-status">Imported PDF entries remain hidden until reviewed and approved by an RVCE academic administrator.</p>
    </form></section>}
  </main>
}
