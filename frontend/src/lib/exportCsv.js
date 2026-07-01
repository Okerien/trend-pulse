// Feature 8 — CSV export. Long format: one row per (keyword, date).
// Region and time range are encoded into the filename.
export function exportCsv({ dates, keywords, range, geo }) {
  const header = ["keyword", "date", "interest", "region", "range"];
  const rows = [header];
  keywords.forEach((kw) => {
    (kw.values || []).forEach((v, i) => {
      rows.push([
        csvCell(kw.keyword),
        dates[i] || "",
        v == null ? "" : v,
        geo,
        range,
      ]);
    });
  });
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `trend-pulse_${geo}_${range}_${new Date()
    .toISOString()
    .slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function csvCell(s) {
  const str = String(s ?? "");
  return /[",\n]/.test(str) ? `"${str.replace(/"/g, '""')}"` : str;
}
