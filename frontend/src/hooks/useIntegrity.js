import { useEffect, useState } from "react";
import { fetchIntegrity } from "../lib/api";

export default function useIntegrity(slug) {
  const [state, setState] = useState({ loading: true, data: null, error: null, notFound: false });

  useEffect(() => {
    if (!slug) {
      setState({ loading: false, data: null, error: null, notFound: false });
      return;
    }
    setState({ loading: true, data: null, error: null, notFound: false });
    fetchIntegrity(slug)
      .then((data) => setState({ loading: false, data, error: null, notFound: false }))
      .catch((error) => {
        if (error.response?.status === 404) {
          setState({ loading: false, data: null, error: null, notFound: true });
        } else {
          setState({ loading: false, data: null, error, notFound: false });
        }
      });
  }, [slug]);

  return state;
}
