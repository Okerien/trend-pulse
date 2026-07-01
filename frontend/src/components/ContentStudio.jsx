import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { loadPlans, savePlan, deletePlan } from "../lib/plans";
import StrategyIntake from "./StrategyIntake";
import StrategyProgress from "./StrategyProgress";
import ContentPlan from "./ContentPlan";
import { Trash, FileText } from "./Icons";

export default function ContentStudio({ onToast }) {
  const [view, setView] = useState("intake"); // intake | analyzing | result
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [plan, setPlan] = useState(null);
  const [intake, setIntake] = useState(null);
  const [saved, setSaved] = useState(loadPlans());
  const poll = useRef(null);

  async function onAnalyze(form) {
    setIntake(form);
    setError(null);
    setPlan(null);
    try {
      const { job_id } = await api.strategy.analyze(form);
      setJobId(job_id);
      setStatus({ stage: "queued", progress: 4 });
      setView("analyzing");
    } catch {
      setError("network");
      setView("analyzing");
    }
  }

  // Poll job status while analyzing.
  useEffect(() => {
    if (view !== "analyzing" || !jobId) return;
    let alive = true;
    async function tick() {
      try {
        const st = await api.strategy.status(jobId);
        if (!alive) return;
        if (st.error) { setError(st.error); return; }
        setStatus(st);
        if (st.done) {
          const result = await api.strategy.result(jobId);
          if (!alive) return;
          setPlan(result);
          const entry = savePlan(form_client(intake), intake, result);
          setSaved(loadPlans());
          setView("result");
          return;
        }
      } catch { /* keep polling */ }
      poll.current = setTimeout(tick, 2500);
    }
    tick();
    return () => { alive = false; clearTimeout(poll.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, jobId]);

  function openSaved(entry) {
    setIntake(entry.intake);
    setPlan(entry.plan);
    setView("result");
  }
  function reset() {
    setView("intake"); setPlan(null); setJobId(null); setStatus(null); setError(null);
  }
  function removeSaved(id) {
    setSaved(deletePlan(id));
  }

  if (view === "analyzing") return <StrategyProgress status={status} error={error} />;
  if (view === "result" && plan)
    return <ContentPlan plan={plan} intake={intake} onReset={reset} onToast={onToast} />;

  return (
    <div className="studio-intake">
      <StrategyIntake onAnalyze={onAnalyze} />
      {saved.length > 0 && (
        <div className="saved-plans">
          <div className="section-title">Saved plans</div>
          <div className="saved-grid">
            {saved.map((p) => (
              <div className="saved-card" key={p.id}>
                <div className="saved-info" onClick={() => openSaved(p)}>
                  <div className="saved-ic"><FileText size={16} /></div>
                  <div>
                    <div className="saved-client">{p.client}</div>
                    <div className="saved-meta num">{new Date(p.createdAt).toLocaleDateString()} · {p.geo}</div>
                  </div>
                </div>
                <button className="iconbtn" title="Delete" onClick={() => removeSaved(p.id)}><Trash size={15} /></button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const form_client = (intake) => intake?.what || intake?.website || "Untitled";
