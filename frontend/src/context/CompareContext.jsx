import { createContext, useCallback, useContext, useEffect, useState } from "react";

export const MAX_COMPARE = 5;
const STORAGE_KEY = "mp_compare_selection";
const CompareContext = createContext(null);

export function CompareProvider({ children }) {
  const [selected, setSelected] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? []; }
    catch { return []; }
  });

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(selected)); }
    catch {}
  }, [selected]);

  const toggleMP = useCallback((mp) => {
    setSelected((prev) => {
      if (prev.some((m) => m.slug === mp.slug)) return prev.filter((m) => m.slug !== mp.slug);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, mp];
    });
  }, []);

  const removeMP = useCallback((slug) => setSelected((prev) => prev.filter((m) => m.slug !== slug)), []);
  const clearAll = useCallback(() => setSelected([]), []);
  const isSelected = useCallback((slug) => selected.some((m) => m.slug === slug), [selected]);

  return (
    <CompareContext.Provider value={{ selected, toggleMP, removeMP, clearAll, isSelected, isFull: selected.length >= MAX_COMPARE }}>
      {children}
    </CompareContext.Provider>
  );
}

export function useCompare() {
  return useContext(CompareContext);
}
