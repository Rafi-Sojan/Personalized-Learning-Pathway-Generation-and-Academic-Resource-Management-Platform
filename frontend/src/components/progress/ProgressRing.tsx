/** Display the learner's completion percentage as a labeled progress ring. */
export function ProgressRing({ percent }: { percent: number }) {
  return <div className="ring"><strong>{percent}%</strong><span>complete</span></div>
}
