// Feature 8 — PNG export of a chart node on a clean white background, for slides.
// Forces a light render even in dark mode (slides are light), then restores.
// html2canvas is loaded lazily to keep it out of the initial bundle.

export async function exportPng(node, filename = "trend-pulse.png") {
  if (!node) return;
  const { default: html2canvas } = await import("html2canvas");

  // Temporarily force a light backdrop + dark text so the exported image reads
  // well on a slide, regardless of the active theme.
  const prevBg = node.style.background;
  const prevColor = node.style.color;
  node.style.background = "#ffffff";
  node.style.color = "#15151d";
  // Darken axis/legend text for the capture.
  const texts = node.querySelectorAll(".recharts-text, .recharts-legend-item-text");
  const prevFills = [];
  texts.forEach((t) => { prevFills.push(t.style.fill); t.style.fill = "#5b6072"; });

  try {
    const canvas = await html2canvas(node, {
      backgroundColor: "#ffffff", scale: 2, logging: false, useCORS: true,
    });
    const link = document.createElement("a");
    link.download = filename;
    link.href = canvas.toDataURL("image/png");
    link.click();
  } finally {
    node.style.background = prevBg;
    node.style.color = prevColor;
    texts.forEach((t, i) => { t.style.fill = prevFills[i]; });
  }
}
