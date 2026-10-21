import { useEffect, useState } from 'react'

export function useAsync<T>(loader: () => Promise<T>, fallback: T) {
  const [data, setData] = useState<T>(fallback)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    loader().then((value) => active && setData(value)).catch((reason: Error) => active && setError(reason.message)).finally(() => active && setLoading(false))
    return () => { active = false }
  }, [loader])

  return { data, loading, error }
}
