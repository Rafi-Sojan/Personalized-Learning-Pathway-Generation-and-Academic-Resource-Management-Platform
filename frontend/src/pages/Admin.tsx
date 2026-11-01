import { useEffect, useState, type FormEvent } from 'react'
import { createManagedUser, getManagedUsers } from '../services/admin'
import { getRvceCatalog, getRvceCourseReview, verifyRvceCourse, type RvceCourseReview, type RvceProgram } from '../services/rvce'
import type { ManagedUser } from '../types'

/** Provide role-managed user administration and the RVCE syllabus review queue. */
export function Admin() {
  const [users, setUsers] = useState<ManagedUser[]>([])
  const [form, setForm] = useState({ email: '', name: '', password: '', role: 'instructor' })
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [review, setReview] = useState<RvceCourseReview[]>([])
  const [programs, setPrograms] = useState<RvceProgram[]>([])
  const [mappings, setMappings] = useState<Record<string, string>>({})
  useEffect(() => {
    getManagedUsers().then(setUsers).catch((reason) => setError(reason instanceof Error ? reason.message : 'Unable to load users'))
    Promise.all([getRvceCourseReview(), getRvceCatalog()]).then(([rows, catalog]) => { setReview(rows); setPrograms(catalog.program_schemes) }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Unable to load RVCE review queue'))
  }, [])
  /** Create a managed account and update the directory without a full-page reload. */
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(null); setMessage(null); try { const user = await createManagedUser(form); setUsers((current) => [...current, user]); setForm({ email: '', name: '', password: '', role: 'instructor' }); setMessage('User created.') } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to create user') } }
  /** Submit the academic decision and remove the resolved candidate from the queue. */
  async function reviewCourse(row: RvceCourseReview, status: 'academic_verified' | 'rejected') {
    setError(null); setMessage(null)
    try {
      const result = await verifyRvceCourse(row.id, status, status === 'academic_verified' && row.program_code === 'BE-UNMAPPED' ? mappings[row.id] : undefined)
      setReview((current) => current.filter((item) => item.id !== result.id))
      setMessage(`${row.course_code} ${status === 'academic_verified' ? 'approved' : 'rejected'}.`)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to update course review') }
  }
  return <main><div className="eyebrow">Platform governance</div><h1>Administration</h1><p className="lede">Manage platform users and review source-backed RVCE syllabus records before they reach learner roadmaps.</p><section className="dashboard-grid"><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Provisioning</span><h2>Create managed user</h2></div></div><form className="form-grid" onSubmit={submit}><label>Name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label><label>Email<input required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label><label>Password<input required minLength={8} type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label><label>Role<select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}><option value="student">Student</option><option value="instructor">Instructor</option><option value="admin">Administrator</option></select></label><button className="primary" type="submit">Create user</button></form></div><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Directory</span><h2>Users</h2></div></div>{users.map((user) => <div className="course-mini" key={user.id}><div className="course-icon">{user.role.slice(0, 2).toUpperCase()}</div><div className="course-copy"><strong>{user.name}</strong><small>{user.email} · {user.role}</small></div></div>)}</div></section>
    <section className="panel" aria-labelledby="rvce-review-heading"><div className="panel-heading"><div><span className="section-kicker">Academic verification</span><h2 id="rvce-review-heading">RVCE syllabus review queue</h2></div><span>{review.length} pending</span></div>{review.length === 0 && <p>No RVCE syllabus records are awaiting review.</p>}{review.map((row) => <article className="course-mini rvce-review-row" key={row.id}><div className="course-icon">{row.course_code.slice(0, 2)}</div><div className="course-copy"><strong>{row.title}</strong><small>{row.course_code} · {row.program_code} · {row.scheme_year} scheme · Semester {row.semester} · {row.credits} credits</small><small>{row.source_filename}, page {row.source_page ?? 'unknown'}</small><small>SHA-256: {row.source_checksum}</small>{row.program_code === 'BE-UNMAPPED' && <label>Branch mapping required<select value={mappings[row.id] ?? ''} onChange={(event) => setMappings((current) => ({ ...current, [row.id]: event.target.value }))}><option value="">Choose RVCE program</option>{programs.map((program) => <option key={program.code} value={program.code}>{program.name} ({program.code})</option>)}</select></label>}<div className="action-row"><button className="primary" type="button" disabled={row.program_code === 'BE-UNMAPPED' && !mappings[row.id]} onClick={() => reviewCourse(row, 'academic_verified')}>Approve</button><button className="secondary" type="button" onClick={() => reviewCourse(row, 'rejected')}>Reject</button></div></div></article>)}</section>{message && <p role="status">{message}</p>}{error && <p className="form-error" role="alert">{error}</p>}</main>
}
