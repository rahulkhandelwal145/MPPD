import { useEffect, useState } from "react";
import { fetchMPs, fetchStatsSummary } from "../lib/api";

export default function useMPs({ party, state: stateFilter, gender, is_minister, is_speaker, is_loa, terms, terms_min, has_criminal_cases, has_serious_cases, is_convicted, is_crorepati, has_mplads, has_statements, has_flagged, search, sort, direction, page, limit }) {
  const [state, setState] = useState({ loading: true, data: null, error: null, summary: null });

  useEffect(() => {
    setState((current) => ({ ...current, loading: true }));
    fetchMPs({ party, state: stateFilter, gender, is_minister, is_speaker, is_loa, terms, terms_min, has_criminal_cases, has_serious_cases, is_convicted, is_crorepati, has_mplads, has_statements, has_flagged, search: search || undefined, sort, direction, page, limit })
      .then((data) => setState((current) => ({ ...current, loading: false, data, error: null })))
      .catch((error) => setState((current) => ({ ...current, loading: false, data: null, error })));
  }, [party, stateFilter, gender, is_minister, is_speaker, is_loa, terms, terms_min, has_criminal_cases, has_serious_cases, is_convicted, is_crorepati, has_mplads, has_statements, has_flagged, search, sort, direction, page, limit]);

  useEffect(() => {
    fetchStatsSummary().then((summary) => setState((current) => ({ ...current, summary }))).catch(() => {});
  }, []);

  return state;
}
