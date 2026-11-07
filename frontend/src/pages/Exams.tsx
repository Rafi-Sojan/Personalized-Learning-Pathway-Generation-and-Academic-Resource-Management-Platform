import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { getConcepts } from '../services/concepts'
import { getCourses } from '../services/courses'
import { getExamFrequency, getExamPaperPdf, getExamQuestions, importExamPaperPdf, reviewExamQuestion } from '../services/exams'
import type { Concept, Course, HistoricalFrequency, HistoricalQuestion } from '../types'

/** Import past-paper PDFs and explore subject topic frequency across exam years. */
export function Exams() {
  const [courses, setCourses] = useState<Course[]>([])
  const [courseId, setCourseId] = useState('')
  const [questions, setQuestions] = useState<HistoricalQuestion[]>([])
  const [concepts, setConcepts] = useState<Concept[]>([])
  const [frequency, setFrequency] = useState<HistoricalFrequency | null>(null)
  const [source, setSource] = useState('University examination')
  const [year, setYear] = useState(String(new Date().getFullYear()))
  const [assessmentType, setAssessmentType] = useState('unknown')
  const [questionFormat, setQuestionFormat] = useState('unknown')
  const [partAIsQuiz, setPartAIsQuiz] = useState(true)
  const [fromYear, setFromYear] = useState('')
  const [toYear, setToYear] = useState('')
  const [search, setSearch] = useState('')
  const [topicFilter, setTopicFilter] = useState('')
  const [assessmentFilter, setAssessmentFilter] = useState('')
  const [formatFilter, setFormatFilter] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [difficultyByQuestion, setDifficultyByQuestion] = useState<Record<string, string>>({})
  const [assessmentByQuestion, setAssessmentByQuestion] = useState<Record<string, string>>({})
  const [formatByQuestion, setFormatByQuestion] = useState<Record<string, string>>({})
  const [conceptByQuestion, setConceptByQuestion] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  /** Load learner-owned subjects and use the first one as the initial filter. */
  useEffect(() => {
    getCourses().then((items) => {
      setCourses(items)
      if (items[0]) setCourseId(items[0].id)
    }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Unable to load subjects'))
  }, [])

  /** Refresh the paper archive and aggregate topic-frequency view for active filters. */
  const refresh = useCallback(async () => {
    if (!courseId) {
      setQuestions([])
      setFrequency(null)
      return
    }
    setLoading(true)
    setError('')
    try {
      const lowerYear = fromYear ? Number(fromYear) : undefined
      const upperYear = toYear ? Number(toYear) : undefined
      const [loadedQuestions, loadedFrequency, loadedConcepts] = await Promise.all([
        getExamQuestions(courseId, lowerYear, upperYear, search.trim() || undefined, assessmentFilter || undefined, formatFilter || undefined, topicFilter.trim() || undefined),
        getExamFrequency(courseId, lowerYear, upperYear, assessmentFilter || undefined),
        getConcepts(courseId),
      ])
      setQuestions(loadedQuestions)
      setFrequency(loadedFrequency)
      setConcepts(loadedConcepts.filter((concept) => concept.review_status === 'verified'))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load question frequency')
    } finally {
      setLoading(false)
    }
  }, [courseId, fromYear, toYear, search, topicFilter, assessmentFilter, formatFilter])

  /** Reload the archive whenever the subject or filter inputs change. */
  useEffect(() => { void refresh() }, [refresh])

  /** Parse and import the selected paper PDF, then refresh its subject statistics. */
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file || !courseId) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const imported = await importExamPaperPdf(courseId, source.trim(), Number(year), file, assessmentType, questionFormat, partAIsQuiz)
      const quizItems = imported.filter((question) => question.question_kind === 'quiz').length
      const mainQuestions = imported.length - quizItems
      setMessage(`Imported ${mainQuestions} main questions and ${quizItems} quiz items from ${file.name}.`)
      setFile(null)
      await refresh()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to parse this paper')
    } finally {
      setBusy(false)
    }
  }

  /** Confirm an extracted question record so it can contribute to evidence-based trends. */
  async function verifyQuestion(question: HistoricalQuestion) {
    try {
      const selectedDifficulty = difficultyByQuestion[question.id]
      const selectedConcept = conceptByQuestion[question.id] ?? question.concept_id ?? ''
      await reviewExamQuestion(question.id, 'verified', selectedDifficulty ? Number(selectedDifficulty) : undefined, assessmentByQuestion[question.id] ?? question.assessment_type, formatByQuestion[question.id] ?? question.question_format, selectedConcept || null)
      await refresh()
      setMessage('Question verified and included in historical frequency evidence.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to verify question') }
  }

  /** Reject a parser row so it cannot contribute to counts or roadmap evidence. */
  async function rejectQuestion(question: HistoricalQuestion) {
    try {
      await reviewExamQuestion(question.id, 'rejected')
      await refresh()
      setMessage('Question extraction rejected and excluded from historical evidence.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to reject question') }
  }

  /** Open the retained original paper at the extracted question's source page. */
  async function openSourcePaper(resourceId: string, page: number | null) {
    const tab = window.open('about:blank', '_blank')
    if (!tab) { setError('Allow pop-ups to open the source PDF.'); return }
    try {
      const blob = await getExamPaperPdf(resourceId)
      const url = URL.createObjectURL(blob)
      tab.location.href = `${url}${page ? `#page=${page}` : ''}`
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (reason) {
      tab.close()
      setError(reason instanceof Error ? reason.message : 'Unable to open source paper')
    }
  }

  /** Return a bounded bar width for the topic count within the current subject. */
  function barWidth(count: number) {
    const maximum = Math.max(...(frequency?.topics.map((topic) => topic.question_count) ?? [1]), 1)
    return `${Math.max(5, (count / maximum) * 100)}%`
  }

  return <main>
    <div className="eyebrow">Past-paper evidence</div>
    <h1>Question frequency</h1>
    <p className="lede">Import subject papers, see which syllabus topics repeat, and track how their frequency changes by year.</p>
    <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Add to the question archive</span><h2>Parse a question-paper PDF</h2></div></div>
      <form className="form-grid" onSubmit={submit}>
        <label>Subject<select required value={courseId} onChange={(event) => setCourseId(event.target.value)}>{courses.map((course) => <option key={course.id} value={course.id}>{course.code} · {course.title}</option>)}</select></label>
        <label>Paper / exam name<input required maxLength={240} value={source} onChange={(event) => setSource(event.target.value)} placeholder="2025 Main Examination" /></label>
        <label>Exam year<input required type="number" min="1900" max="2100" value={year} onChange={(event) => setYear(event.target.value)} /></label>
        <label>Assessment type<select value={assessmentType} onChange={(event) => setAssessmentType(event.target.value)}><option value="quiz">Quiz</option><option value="test">Test / CIE</option><option value="see">SEE</option><option value="assignment">Assignment</option><option value="lab">Lab</option><option value="practice">Practice</option><option value="unknown">Unknown</option></select></label>
        <label>Question format<select value={questionFormat} onChange={(event) => setQuestionFormat(event.target.value)}><option value="unknown">Unspecified / mixed</option><option value="objective">Objective</option><option value="short">Short answer</option><option value="long">Long answer</option><option value="numerical">Numerical</option><option value="coding">Coding</option><option value="practical">Practical</option></select></label>
        <label className="checkbox-label"><input type="checkbox" checked={partAIsQuiz} onChange={(event) => setPartAIsQuiz(event.target.checked)} /> Part A is the quiz section</label>
        <label>PDF file<input required type="file" accept="application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
        <small>Printed CIE/SEE and Part A/Part B headings take precedence; the selected metadata is used when the PDF does not declare them. Imported questions remain pending review.</small>
        <button className="primary" type="submit" disabled={!courseId || !file || busy}>{busy ? 'Parsing paper…' : 'Import paper'}</button>
      </form>
      {!courses.length && <p className="empty-state">Add a subject before importing its papers.</p>}
    </section>

    <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Subject analytics</span><h2>{frequency?.mapped_main_question_count ?? 0} mapped main questions · {frequency?.unmapped_main_question_count ?? 0} awaiting a topic · {frequency?.quiz_count ?? 0} quiz items</h2></div><span className="section-kicker">Verified syllabus-topic frequency</span></div>
      <div className="form-grid exam-filters">
        <label>Subject<select value={courseId} onChange={(event) => setCourseId(event.target.value)}>{courses.map((course) => <option key={course.id} value={course.id}>{course.code} · {course.title}</option>)}</select></label>
        <label>From year<input type="number" min="1900" max="2100" value={fromYear} onChange={(event) => setFromYear(event.target.value)} placeholder="All years" /></label>
        <label>Through year<input type="number" min="1900" max="2100" value={toYear} onChange={(event) => setToYear(event.target.value)} placeholder="Latest" /></label>
        <label>Find in question text<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search the archive" /></label>
        <label>Topic<input value={topicFilter} onChange={(event) => setTopicFilter(event.target.value)} placeholder="Mapped topic" /></label>
        <label>Assessment type<select value={assessmentFilter} onChange={(event) => setAssessmentFilter(event.target.value)}><option value="">All types</option><option value="quiz">Quiz</option><option value="test">Test / CIE</option><option value="see">SEE</option><option value="assignment">Assignment</option><option value="lab">Lab</option><option value="practice">Practice</option><option value="unknown">Unknown</option></select></label>
        <label>Question format<select value={formatFilter} onChange={(event) => setFormatFilter(event.target.value)}><option value="">All formats</option><option value="objective">Objective</option><option value="short">Short answer</option><option value="long">Long answer</option><option value="numerical">Numerical</option><option value="coding">Coding</option><option value="practical">Practical</option><option value="unknown">Unknown</option></select></label>
      </div>
      {loading && <p aria-live="polite">Updating subject statistics…</p>}
      {frequency?.topics.length ? <div className="exam-frequency-list">{frequency.topics.map((topic) => <article className="exam-frequency-row" key={topic.topic_key}>
        <div className="exam-frequency-heading"><strong>{topic.topic_name}</strong><span>{topic.question_count} question{topic.question_count === 1 ? '' : 's'} · {topic.last_seen} last asked</span></div>
        <div className="exam-frequency-track" aria-label={`${topic.question_count} questions`}><i style={{ width: barWidth(topic.question_count) }} /></div>
        <div className="exam-year-list">{topic.year_counts.map((item) => <span key={item.year}>{item.year}: {item.count}</span>)}</div>
        <small>{topic.total_marks ? `${topic.total_marks} total documented marks · ` : ''}Evidence: {topic.supporting_questions.map((question, index) => <span key={question.id}>{index > 0 ? ', ' : ''}<a href={`#question-${question.id}`}>{question.year}{question.source_page ? ` p.${question.source_page}` : ''}</a></span>)}</small>
        {topic.repeat_count > 0 && <small className="exam-repeat-count">{topic.repeat_count} repeated question occurrence{topic.repeat_count === 1 ? '' : 's'}</small>}
      </article>)}</div> : !loading && <p className="empty-state">No verified, concept-mapped main questions match this subject and year range. Review the extracted rows and assign syllabus topics first.</p>}
    </section>

    <section className="panel">
      <div className="panel-heading"><div><span className="section-kicker">Searchable records</span><h2>Question archive</h2></div><span className="section-kicker">{questions.length} shown</span></div>
      {questions.length ? questions.slice(0, 100).map((question) => <article className="roadmap-row" id={`question-${question.id}`} key={question.id}>
        <span className="roadmap-number">{question.exam_year}</span>
        <div><strong>{question.question_number ? `${question.question_number}${question.subpart ? `(${question.subpart})` : ''}. ` : ''}{question.prompt}</strong><p>{question.source_document || question.source} · {question.source_page ? `p. ${question.source_page} · ` : ''}{question.paper_part ? `Part ${question.paper_part} · ` : ''}{question.question_kind === 'quiz' ? 'Quiz item' : 'Main question'} · {question.assessment_type} · {question.question_format}{question.marks !== null ? ` · ${question.marks} marks` : ''}{question.difficulty !== null ? ` · difficulty ${question.difficulty}/5` : ''} · {question.topic_label} · {question.review_status}</p>
          {question.review_status === 'pending_review' && question.mapping_metadata.explanation && <p className="mapping-evidence"><strong>Mapping engine:</strong> {question.mapping_metadata.explanation}{question.mapping_confidence !== null ? ` Best score ${Math.round(question.mapping_confidence * 100)}%.` : ''}{question.mapping_metadata.candidates?.length ? ` Candidates: ${question.mapping_metadata.candidates.slice(0, 3).map((candidate) => `${candidate.name ?? candidate.concept_id}${candidate.score !== undefined ? ` ${Math.round(candidate.score * 100)}%` : ''}`).join(', ')}.` : ''} Review this suggestion against the source before verification.</p>}
          {question.source_resource_id && <button className="secondary" type="button" onClick={() => void openSourcePaper(question.source_resource_id!, question.source_page)}>Open original PDF{question.source_page ? ` · page ${question.source_page}` : ''}</button>}
          {question.review_status === 'pending_review' && <><div className="form-grid"><label>Syllabus concept<select value={conceptByQuestion[question.id] ?? question.concept_id ?? ''} onChange={(event) => setConceptByQuestion((current) => ({ ...current, [question.id]: event.target.value }))}><option value="">Unmapped · exclude from topic frequency</option>{concepts.map((concept) => <option key={concept.id} value={concept.id}>{concept.unit_label ? `${concept.unit_label} · ` : ''}{concept.name}</option>)}</select></label><label>Assessment type<select value={assessmentByQuestion[question.id] ?? question.assessment_type} onChange={(event) => setAssessmentByQuestion((current) => ({ ...current, [question.id]: event.target.value }))}><option value="quiz">Quiz</option><option value="test">Test / CIE</option><option value="see">SEE</option><option value="assignment">Assignment</option><option value="lab">Lab</option><option value="practice">Practice</option><option value="unknown">Unknown</option></select></label><label>Question format<select value={formatByQuestion[question.id] ?? question.question_format} onChange={(event) => setFormatByQuestion((current) => ({ ...current, [question.id]: event.target.value }))}><option value="unknown">Unknown / mixed</option><option value="objective">Objective</option><option value="short">Short answer</option><option value="long">Long answer</option><option value="numerical">Numerical</option><option value="coding">Coding</option><option value="practical">Practical</option></select></label><label>Difficulty, if reviewed<select aria-label={`Difficulty for question ${question.question_number ?? question.id}`} value={difficultyByQuestion[question.id] ?? ''} onChange={(event) => setDifficultyByQuestion((current) => ({ ...current, [question.id]: event.target.value }))}><option value="">Unrated</option><option value="1">1 · Very easy</option><option value="2">2 · Easy</option><option value="3">3 · Moderate</option><option value="4">4 · Hard</option><option value="5">5 · Very hard</option></select></label></div><button className="secondary" type="button" onClick={() => void verifyQuestion(question)}>Verify record</button> <button className="secondary" type="button" onClick={() => void rejectQuestion(question)}>Reject extraction</button></>}</div>
      </article>) : <p className="empty-state">No questions in the selected archive view.</p>}
    </section>
    {message && <p role="status">{message}</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
  </main>
}
