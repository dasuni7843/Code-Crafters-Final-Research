import { useCallback, useEffect, useRef, useState } from 'react'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

// Runs an async loader on demand and tracks loading/error state.
export function useAsyncAction<TArgs extends unknown[], TData>(
  action: (...args: TArgs) => Promise<TData>,
) {
  const [state, setState] = useState<AsyncState<TData>>({
    data: null,
    loading: false,
    error: null,
  })
  const mounted = useRef(true)
  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const execute = useCallback(
    async (...args: TArgs) => {
      setState({ data: null, loading: true, error: null })
      try {
        const data = await action(...args)
        if (mounted.current) setState({ data, loading: false, error: null })
        return data
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Something went wrong.'
        if (mounted.current) setState({ data: null, loading: false, error: message })
        return null
      }
    },
    [action],
  )

  const reset = useCallback(() => setState({ data: null, loading: false, error: null }), [])

  return { ...state, execute, reset }
}

// Loads data once on mount.
export function useApiOnMount<TData>(loader: () => Promise<TData>) {
  const [state, setState] = useState<AsyncState<TData>>({
    data: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    let active = true
    setState({ data: null, loading: true, error: null })
    loader()
      .then((data) => {
        if (active) setState({ data, loading: false, error: null })
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : 'Something went wrong.'
        if (active) setState({ data: null, loading: false, error: message })
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return state
}
