export function QuizCard({ question }: { question: string }) {
  return <article className="quiz-card"><span className="section-kicker">Quick check</span><h2>{question}</h2><button className="primary">Start quiz</button></article>
}
