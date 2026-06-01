import { useEffect, useState } from "react";
import { fetchLeaderboard } from "../lib/api";

export default function useLeaderboard(metric, direction, limit = 20) {
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    setState({ loading: true, data: null, error: null });
    fetchLeaderboard({ metric, direction, limit })
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => setState({ loading: false, data: null, error }));
  }, [metric, direction, limit]);

  return state;
}
