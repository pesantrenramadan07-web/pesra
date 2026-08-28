export function formatMasehi(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return new Intl.DateTimeFormat("id-ID", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  }).format(d);
}

export function formatHijri(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  try {
    return new Intl.DateTimeFormat("id-TN-u-ca-islamic-umalqura", {
      day: "numeric", month: "long", year: "numeric",
    }).format(d) + " H";
  } catch {
    return "";
  }
}

export function shortDate(dateStr) {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return new Intl.DateTimeFormat("id-ID", { day: "2-digit", month: "short", year: "numeric" }).format(d);
}

export function dateTime(dateStr) {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
  }).format(d);
}
