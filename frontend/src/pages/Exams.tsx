import { useCallback, useEffect, useState } from 'react'
import { getCourses } from '../services/courses'
import { getExamQuestions, getExamRankings, importExamQuestions } from '../services/exams'
import type { Course, HistoricalQuestion, HistoricalRanking } from '../types'

export function Exams() {
  const [courses, setCourses] = useState<Course[]>([])
  const [courseId, setCourseId] = useState('')
  const [questions, setQuestions] = useState<HistoricalQuestion[]>([])
  const [rankings, setRankings] = useState<HistoricalRanking[]>([])
  const [source, setSource] = useState('')
  const [year, setYear] = useState(String(new Date().getFullYear()))
  const [text, setText] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async (selected: string) => {
    if (!selected) return
    try { const [loadedQuestions, loadedRankings] = await Promise.all([getExamQuestions(selected), getExamRankings(selected)]); setQuestions(loadedQuestions); setRankings(loadedRankings) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to load exam data') }
  }, [])

  useEffect(() => { getCourses().then((items) => { setCourses(items); if (items[0]) setCourseId(items[0].id) }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Unable to load courses')) }, [])
  useEffect(() => { void refresh(courseId) }, [courseId, refresh])

  async function submit(event: React.FormEvent) {
    event.preventDefault(); setError(null); setMessage(null)
    try { await importExamQuestions({ course_id: courseId, source, exam_year: Number(year), text }); setMessage('Question paper imported.'); setText(''); await refresh(courseId) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to import questions') }
  }

  return <main><div className="eyebrow">Evidence-based preparation</div><h1>Historical exams</h1><p className="lede">Import question papers and see which concepts appear most often.</p><section className="panel"><div className="panel-heading"><div><span className="section-kicker">Instructor workspace</span><h2>Import a question paper</h2></div></div><form className="roadmap-controls form-grid" onSubmit={submit}><label>Course<select value={courseId} onChange={(event) => setCourseId(event.target.value)}>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select></label><label>Source<input required value={source} onChange={(event) => setSource(event.target.value)} placeholder="University paper" /></label><label>Year<input required type="number" min="1900" max="2100" value={year} onChange={(event) => setYear(event.target.value)} /></label><label className="full-field">Questions<textarea required rows={7} value={text} onChange={(event) => setText(event.target.value)} placeholder="1. Explain functions.\n2. Describe control flow." /></label><button className="primary" type="submit" disabled={!courseId}>Import questions</button></form></section><section className="dashboard-grid"><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Coverage</span><h2>Concept ranking</h2></div></div>{rankings.length ? rankings.map((item) => <div className="course-mini" key={item.concept_id}><div className="course-icon">{item.question_count}</div><div className="course-copy"><strong>{item.concept_name}</strong><small>{item.question_count} questions · difficulty {item.average_difficulty}</small></div></div>) : <p className="empty-state">No mapped exam questions yet.</p>}</div><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Imported records</span><h2>Question papers</h2></div></div>{questions.length ? questions.slice(0, 10).map((question) => <div className="roadmap-row" key={question.id}><span className="roadmap-number">{question.exam_year}</span><div><strong>{question.prompt}</strong><p>{question.source} · {question.topic_label}</p></div></div>) : <p className="empty-state">Import a paper to begin.</p>}</div></section>{message && <p role="status">{message}</p>}{error && <p className="form-error" role="alert">{error}</p>}</main>
}
