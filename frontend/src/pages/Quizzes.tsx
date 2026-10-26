import { useState } from 'react'
import { submitQuizAttempt } from '../services/quizzes'

export function Quizzes() {
  const [answer, setAnswer] = useState<number | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  async function submit() {
    if (answer === null) return
    setBusy(true)
    try { const response = await submitQuizAttempt('control-flow', answer); setResult(response.correct ? 'Correct. Your progress has been updated.' : 'Not quite. Review the concept and try again.') } catch { setResult('Unable to submit the attempt right now.') } finally { setBusy(false) }
  }
  return <main><div className="eyebrow">Check your understanding</div><h1>Quizzes</h1><p className="lede">Short practice sessions that turn recognition into recall.</p><div className="quiz-card"><span className="section-kicker">Up next · Control Flow</span><h2>Which statement best describes control flow?</h2><div className="options">{['How a program chooses what to execute', 'How a database stores records', 'How a server is deployed'].map((option, index) => <button className={answer === index ? 'selected' : ''} onClick={() => setAnswer(index)} key={option}>{String.fromCharCode(65 + index)}. {option}</button>)}</div>{result && <div className="form-error">{result}</div>}<button className="primary" onClick={submit} disabled={answer === null || busy}>{busy ? 'Submitting…' : 'Submit answer'}</button></div></main>
}
