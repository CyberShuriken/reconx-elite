import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getTargetById, updateTargetNotes } from "../lib/supabase";

export default function SupabaseTargetPage() {
  const { targetId } = useParams();
  const [target, setTarget] = useState(null);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadTarget() {
      setIsLoading(true);
      try {
        const row = await getTargetById(targetId);
        if (!cancelled) {
          setTarget(row);
          setNotes(row.notes || "");
          setError("");
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message || "Failed to load target");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadTarget();
    return () => {
      cancelled = true;
    };
  }, [targetId]);

  async function saveNotes() {
    setIsSaving(true);
    try {
      const updated = await updateTargetNotes(targetId, notes);
      setTarget(updated);
      setError("");
    } catch (requestError) {
      setError(requestError.message || "Could not save target notes");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <main className="page-shell">
        <div className="panel-card">Loading target...</div>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <Link className="primary-button" to="/">
            Back to dashboard
          </Link>
          <h1>{target?.domain || "Target"}</h1>
          <p className="lede">
            Hosted mode uses Supabase for authentication, targets, notes, and notifications.
          </p>
        </div>
      </header>

      {error ? <p className="error-text panel-card">{error}</p> : null}

      <section className="layout-grid">
        <article className="panel-card">
          <h2>Target notes</h2>
          <textarea
            className="notes-area"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Capture scope notes, ownership context, or next actions here."
            rows={8}
          />
          <button className="primary-button" disabled={isSaving} onClick={saveNotes} type="button">
            {isSaving ? "Saving..." : "Save notes"}
          </button>
        </article>

        <article className="panel-card">
          <h2>Hosted deployment status</h2>
          <p className="muted-copy">
            The Vercel deployment is wired to Supabase for the user-facing dashboard flow.
          </p>
          <ul className="stack-list">
            <li className="list-row">
              <strong>Target storage</strong>
              <span>Active</span>
            </li>
            <li className="list-row">
              <strong>Notifications</strong>
              <span>Active</span>
            </li>
            <li className="list-row">
              <strong>Heavy scan workers</strong>
              <span>Local/Docker mode only</span>
            </li>
          </ul>
        </article>
      </section>
    </main>
  );
}

