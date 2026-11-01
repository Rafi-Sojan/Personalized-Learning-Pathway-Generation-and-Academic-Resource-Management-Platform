type Props = { label: string; value: string; detail: string; tone?: 'accent' | 'warm' | 'cool' }

/** Present one dashboard statistic with its supporting detail and visual tone. */
export function StatCard({ label, value, detail, tone = 'accent' }: Props) {
  return <article className={`stat-card ${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>
}
