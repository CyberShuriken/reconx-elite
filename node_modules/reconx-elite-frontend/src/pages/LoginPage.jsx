import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { formatApiErrorDetail } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

  const navigate = useNavigate();
  const { login, register } = useAuth();

  function handleMouseMove(e) {
    const { clientX, clientY } = e;
    const { innerWidth, innerHeight } = window;
    setMousePos({
      x: (clientX / innerWidth) * 100,
      y: (clientY / innerHeight) * 100,
    });
  }

  function validatePassword(pwd) {
    if (pwd.length < 12) return "Password must be at least 12 characters long";
    if (!/[A-Z]/.test(pwd)) return "Password must contain at least one uppercase letter";
    if (!/[a-z]/.test(pwd)) return "Password must contain at least one lowercase letter";
    if (!/\d/.test(pwd)) return "Password must contain at least one number";
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pwd))
      return "Password must contain at least one special character";
    return null;
  }

  async function onSubmit(event) {
    event.preventDefault();
    if (mode === "register") {
      const pwdError = validatePassword(password);
      if (pwdError) {
        setError(pwdError);
        return;
      }
    }

    setIsSubmitting(true);
    setError("");
    try {
      if (mode === "register") {
        await register({ email, password });
      } else {
        await login({ email, password });
      }
      navigate("/", { replace: true });
    } catch (requestError) {
      const detail = requestError.response?.data?.detail || requestError.message;
      setError(formatApiErrorDetail(detail) || "Authentication failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main
      className="auth-shell"
      onMouseMove={handleMouseMove}
      style={{ "--mouse-x": `${mousePos.x}%`, "--mouse-y": `${mousePos.y}%` }}
    >
      <div className="auth-background"></div>
      <div className="auth-shapes">
        <div
          className="auth-shape"
          style={{ top: "10%", left: "10%", width: "350px", height: "350px" }}
        ></div>
        <div
          className="auth-shape"
          style={{
            top: "65%",
            left: "85%",
            width: "450px",
            height: "450px",
            animationDelay: "-5s",
          }}
        ></div>
        <div
          className="auth-shape"
          style={{
            top: "35%",
            left: "45%",
            width: "300px",
            height: "300px",
            animationDelay: "-10s",
          }}
        ></div>
      </div>

      <div className="auth-container">
        <section className="auth-panel">
          <p className="eyebrow">ReconX Elite</p>
          <h1>Operate your recon pipeline with a clean attack-surface view.</h1>
          <p className="auth-copy">
            Use this platform only against infrastructure you own or are explicitly authorized to
            assess.
          </p>
        </section>

        <section className="auth-card-wrap">
          <div className="auth-card">
            <form onSubmit={onSubmit}>
              <h2>{mode === "register" ? "Create account" : "Sign in"}</h2>
              <label>
                Email
                <input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="hunter@team.example"
                  type="email"
                  required
                />
              </label>
              <label>
                Password
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  type="password"
                  minLength="12"
                  required
                />
              </label>
              {error ? <p className="error-text">{error}</p> : null}
              <button className="primary-button" disabled={isSubmitting} type="submit">
                {isSubmitting ? "Working..." : "Submit"}
              </button>
            </form>
            <button
              className="ghost-button"
              onClick={() => setMode(mode === "register" ? "login" : "register")}
              type="button"
            >
              {mode === "register" ? "Already have an account?" : "Need an account?"}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
