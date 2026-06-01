import { useEffect, useState } from "react";
import { fetchMP } from "../lib/api";

export default function useMP(slug) {
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    if (!slug) {
      setState({ loading: false, data: null, error: null });
      return;
    }
    setState({ loading: true, data: null, error: null });
    fetchMP(slug)
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => setState({ loading: false, data: null, error }));
  }, [slug]);

  return state;
}
