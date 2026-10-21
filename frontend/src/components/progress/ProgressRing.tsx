export function ProgressRing({ percent }: { percent: number }) {
  return <div className="ring"><strong>{percent}%</strong><span>complete</span></div>
}
