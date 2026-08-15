"use strict";

const NS = "http://www.w3.org/2000/svg";
const colors = ["#1565c0", "#c62828", "#2e7d32", "#6a1b9a", "#ef6c00", "#00838f"];

function element(name, attributes = {}) {
  const node = document.createElementNS(NS, name);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
  return node;
}

function render(payload) {
  const host = document.getElementById("chart");
  const legend = document.getElementById("legend");
  const allPoints = payload.series.flatMap((series) => series.points);
  if (!allPoints.length) { host.textContent = "No chart data available."; return; }
  const years = allPoints.map((point) => point.year);
  const shares = allPoints.map((point) => point.share);
  const minYear = Math.min(...years), maxYear = Math.max(...years);
  const minShare = Math.min(0, ...shares), maxShare = Math.max(...shares);
  const svg = element("svg", {viewBox: "0 0 900 420", "aria-hidden": "true"});
  const x = (year) => 55 + ((year - minYear) / Math.max(1, maxYear - minYear)) * 815;
  const y = (share) => 380 - ((share - minShare) / Math.max(0.000001, maxShare - minShare)) * 340;
  svg.append(element("line", {x1: 55, y1: 20, x2: 55, y2: 380, class: "axis"}));
  svg.append(element("line", {x1: 55, y1: 380, x2: 870, y2: 380, class: "axis"}));
  payload.series.forEach((series, index) => {
    const color = colors[index % colors.length];
    const points = series.points.map((point) => `${x(point.year)},${y(point.share)}`).join(" ");
    svg.append(element("polyline", {points, class: "series", stroke: color}));
    const key = document.createElement("span");
    key.className = "key";
    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.backgroundColor = color;
    key.append(swatch, document.createTextNode(series.entity));
    legend.append(key);
  });
  host.replaceChildren(svg);
}

fetch("/api/chart-data", {headers: {Accept: "application/json"}})
  .then((response) => { if (!response.ok) throw new Error(); return response.json(); })
  .then(render)
  .catch(() => { document.getElementById("chart").textContent = "Chart data is unavailable."; });
