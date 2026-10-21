type Props = { label: string; value: string; detail: string; tone?: 'accent' | 'warm' | 'cool' }

export function StatCard({ label, value, detail, tone = 'accent' }: Props) {
  return <article className={`stat-card ${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>
}
