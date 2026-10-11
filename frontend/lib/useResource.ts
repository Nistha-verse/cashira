"use client";
import { useCallback, useEffect, useState } from "react";

// Every request is keyed by identity/language/filters. Previous responses cannot
// overwrite a new identity's view or briefly reveal stale data on navigation.
export function useResource<T>(key: string, load: () => Promise<T>) {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<{ key: string; data?: T; error?: Error; loading: boolean }>({ key, loading: true });
  useEffect(() => {
    let current = true;
    setState({ key, loading: true });
    load().then(data => { if (current) setState({ key, data, loading: false }); }).catch(error => { if (current) setState({ key, error, loading: false }); });
    return () => { current = false; };
  }, [key, load, revision]);
  const refresh = useCallback(() => setRevision(value => value + 1), []);
  return { ...(state.key === key ? state : { loading: true, data: undefined, error: undefined }), refresh };
}
