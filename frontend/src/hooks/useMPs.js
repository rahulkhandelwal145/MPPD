import { useEffect, useState } from "react";
import { fetchMPs, fetchStatsSummary } from "../lib/api";

export default function useMPs({ party, is_minister, sort, direction, page, limit }) {
  const [state, setState] = useState({ loading: true, data: null, error: null, summary: null });

  useEffect(() => {
    setState((current) => ({ ...current, loading: true }));
    fetchMPs({ party, is_minister, sort, direction, page, limit })
      .then((data) => setState((current) => ({ ...current, loading: false, data, error: null })))
      .catch((error) => setState((current) => ({ ...current, loading: false, data: null, error })));
  }, [party, is_minister, sort, direction, page, limit]);

  useEffect(() => {
    fetchStatsSummary().then((summary) => setState((current) => ({ ...current, summary }))).catch(() => {});
  }, []);

  return state;
}
