import type { Resource } from '../../types'

export function ResourceCard({ resource }: { resource: Resource }) {
  return <article className="resource-card"><span>{resource.kind.toUpperCase()} · {resource.duration_minutes} MIN</span><h2>{resource.title}</h2><a href={resource.url} target="_blank" rel="noreferrer">Open resource →</a></article>
}
