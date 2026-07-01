// Per-client saved content plans, in localStorage (agency serves many clients).
const KEY = "trendpulse.plans.v1";

export function loadPlans() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || [];
  } catch {
    return [];
  }
}

export function savePlan(client, intake, plan) {
  const plans = loadPlans();
  const entry = {
    id: Date.now().toString(36),
    client: client || intake.website || "Untitled",
    website: intake.website,
    geo: intake.geo,
    createdAt: Date.now(),
    intake,
    plan,
  };
  // Keep newest first; cap at 30 so localStorage doesn't bloat.
  const next = [entry, ...plans].slice(0, 30);
  localStorage.setItem(KEY, JSON.stringify(next));
  return entry;
}

export function deletePlan(id) {
  const next = loadPlans().filter((p) => p.id !== id);
  localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
