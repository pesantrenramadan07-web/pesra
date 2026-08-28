import React, { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const PeriodContext = createContext(null);

export function PeriodProvider({ children }) {
  const { user } = useAuth();
  const [periods, setPeriods] = useState([]);
  const [activePeriod, setActivePeriod] = useState(null);

  const load = async () => {
    try {
      // /periods/options is available to ALL authenticated users (not gated by PERIOD_VIEW)
      const { data } = await api.get("/periods/options");
      const items = data || [];
      setPeriods(items);
      const active = items.find((p) => p.status === "ACTIVE" && !p.is_test);
      setActivePeriod((cur) => cur || active || items[0] || null);
    } catch {
      setPeriods([]);
    }
  };

  useEffect(() => {
    if (user) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  return (
    <PeriodContext.Provider value={{ periods, activePeriod, setActivePeriod, reloadPeriods: load }}>
      {children}
    </PeriodContext.Provider>
  );
}

export const usePeriod = () => useContext(PeriodContext);
