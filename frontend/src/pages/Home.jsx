import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAuthStatus } from "../api/searchApi";
import "../styles/Home.css";

/**
 * Public homepage for brand / OAuth verification: describes the product,
 * links to the same /privacy URL as the Google OAuth consent screen.
 */
export default function Home() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    getAuthStatus()
      .then((data) => {
        if (data.logged_in) {
          setUser({ name: data.name, email: data.email });
        }
      })
      .finally(() => setAuthLoading(false));
  }, []);

  return (
    <div className="home-page">
      <header className="home-topbar">
        <div className="home-brand">
          <Link to="/">Mirrulations</Link>
        </div>
        <nav className="home-nav" aria-label="Primary">
          <Link className="home-btn home-btn-ghost" to="/privacy">
            Privacy Policy
          </Link>
          {!authLoading && user ? (
            <>
              <span className="home-greeting" title={user.email}>
                Hi, {user.name}
              </span>
              <Link className="home-btn home-btn-primary" to="/explorer">
                Open Explorer
              </Link>
              <Link className="home-btn home-btn-secondary" to="/collections">
                My Collections
              </Link>
              <a className="home-btn home-btn-ghost" href="/logout">
                Sign out
              </a>
            </>
          ) : (
            <>
              <a className="home-btn home-btn-google" href="/login">
                <span className="home-google-icon" aria-hidden>
                  <svg viewBox="0 0 48 48" width={20} height={20}>
                    <path
                      fill="#EA4335"
                      d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
                    />
                    <path
                      fill="#4285F4"
                      d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
                    />
                    <path
                      fill="#34A853"
                      d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
                    />
                  </svg>
                </span>
                Sign in with Google
              </a>
              <Link className="home-btn home-btn-secondary" to="/explorer">
                Explorer
              </Link>
            </>
          )}
        </nav>
      </header>

      <main className="home-main">
        <section className="home-hero" aria-labelledby="home-hero-title">
          <p className="home-eyebrow">Regulatory docket search</p>
          <h1 id="home-hero-title" className="home-title">
            Mirrulations Explorer
          </h1>
          <p className="home-lead">
            Search and explore federal regulatory dockets: full-text search,
            filters by agency, date range, docket type, and CFR references, plus
            sorting to navigate large rulemakings. Save dockets to collections and,
            when enabled for your account, request data exports tied to your sign-in.
          </p>
        </section>

        <section className="home-features" aria-labelledby="home-features-title">
          <h2 id="home-features-title" className="home-section-title">
            What you can do
          </h2>
          <ul className="home-feature-list">
            <li>
              <strong>Search</strong> the corpus with optional advanced filters and
              relevance or count-based sort options.
            </li>
            <li>
              <strong>Collections</strong> keep a personal list of docket IDs linked
              to your account.
            </li>
            <li>
              <strong>Sign-in with Google</strong> identifies you in the app so
              search, collections, and downloads respect your permissions.
            </li>
          </ul>
        </section>

        <section className="home-auth" aria-labelledby="home-auth-title">
          <h2 id="home-auth-title" className="home-section-title">
            Privacy &amp; Google data
          </h2>
          <p className="home-auth-copy">
            We request Google OAuth scopes for sign-in only (OpenID Connect, email,
            and basic profile). How we use and store that data—including Limited Use
            commitments—is described in our{" "}
            <Link className="home-privacy-link" to="/privacy">
              Privacy Policy
            </Link>
            . Use the same policy URL on your Google Cloud OAuth consent screen.
          </p>
        </section>

        <section className="home-legal" aria-labelledby="home-legal-title">
          <h2 id="home-legal-title" className="home-section-title">
            Policies
          </h2>
          <p className="home-legal-copy">
            Use of Google APIs is also governed by the{" "}
            <a
              className="home-privacy-link"
              href="https://developers.google.com/terms/api-services-user-data-policy"
              rel="noopener noreferrer"
            >
              Google API Services User Data Policy
            </a>
            .
          </p>
          <p className="home-legal-copy">
            <Link className="home-privacy-link" to="/privacy">
              Privacy Policy
            </Link>
          </p>
        </section>
      </main>

      <footer className="home-footer">
        <span>Mirrulations Explorer</span>
        <span className="home-footer-sep" aria-hidden>
          ·
        </span>
        <Link to="/privacy">Privacy Policy</Link>
      </footer>
    </div>
  );
}
