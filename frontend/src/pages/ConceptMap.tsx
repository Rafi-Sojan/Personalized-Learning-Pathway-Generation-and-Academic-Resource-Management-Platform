import { useCallback } from 'react'
import { ConceptMapView } from '../components/concept-map/ConceptMapView'
import { useAsync } from '../hooks/useAsync'
import { getConcepts } from '../services/concepts'

export function ConceptMap() {
  const { data, loading } = useAsync(useCallback(() => getConcepts(), []), [])
  return <main><div className="eyebrow">Understand the connections</div><h1>Concept map</h1><p className="lede">See how today’s topic fits into the bigger picture.</p><div className="panel"><div className="panel-heading"><div><span className="section-kicker">Python Foundations</span><h2>Learning dependencies</h2></div><span className="legend"><i /> Complete <i className="current" /> Current <i className="next" /> Next</span></div>{loading ? <p>Loading concepts…</p> : <ConceptMapView concepts={data} />}</div></main>
}
