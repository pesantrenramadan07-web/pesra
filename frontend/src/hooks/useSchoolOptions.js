import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function useSchoolOptions() {
  const [options, setOptions] = useState([]);
  useEffect(() => {
    let ok = true;
    api.get("/schools", { params: { limit: 200, status: "ACTIVE" } })
      .then(({ data }) => { if (ok) setOptions((data.items || []).map((s) => ({ value: s.id, label: s.name }))); })
      .catch(() => {});
    return () => { ok = false; };
  }, []);
  return options;
}
