import { useMemo, useState } from 'react'
import './styles/app.css'
import { searchDockets } from './api/searchApi'

function CollapsibleSection({ title, defaultOpen = true, children, right }) {
    const [open, setOpen] = useState(defaultOpen);
  
    return (
      <section className="section">
        <button
          type="button"
          className="sectionHeader"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
        >
          <span className="sectionTitle">{title}</span>
          <span className="sectionRight">
            {right}
            <span className="sectionChev" aria-hidden="true">{open ? "▾" : "▸"}</span>
          </span>
        </button>
  
        {open && <div className="sectionBody">{children}</div>}
      </section>
    );
  }

export default function App() {
  const [query, setQuery] = useState('')
  const [docType, setDocType] = useState('') // maps to existing "filter" param
  const [agency, setAgency] = useState('')   // maps to existing "agency" param
  const [results, setResults] = useState([])

  // Advanced filters (demo UI)
  const [advOpen, setAdvOpen] = useState(true)
  const [yearFrom, setYearFrom] = useState('')
  const [yearTo, setYearTo] = useState('')
  const [agencySearch, setAgencySearch] = useState('')
  const [selectedAgencies, setSelectedAgencies] = useState(() => new Set())
  const [status, setStatus] = useState(() => new Set())

  const TOP_AGENCIES = useMemo(
    () => [
      { code: 'EPA', name: 'Environmental Protection Agency' },
      { code: 'HHS', name: 'Health and Human Services' },
      { code: 'FDA', name: 'Food and Drug Administration' },
      { code: 'CMS', name: 'Centers for Medicare & Medicaid Services' },
      { code: 'DOT', name: 'Department of Transportation' },
      { code: 'FCC', name: 'Federal Communications Commission' },
    ],
    []
  )

  const ALL_AGENCIES = useMemo(
    () => [
      ...TOP_AGENCIES,
      { code: 'DOL', name: 'Department of Labor' },
      { code: 'DOE', name: 'Department of Energy' },
      { code: 'USDA', name: 'Department of Agriculture' },
      { code: 'SEC', name: 'Securities and Exchange Commission' },
      { code: 'FTC', name: 'Federal Trade Commission' },
      { code: 'NOAA', name: 'National Oceanic and Atmospheric Administration' },
      { code: 'NHTSA', name: 'National Highway Traffic Safety Administration' },
    ],
    [TOP_AGENCIES]
  )

  const agenciesToShow = useMemo(() => {
    const q = agencySearch.trim().toLowerCase()
    if (!q) return TOP_AGENCIES
    return ALL_AGENCIES.filter(
      (a) => a.code.toLowerCase().includes(q) || a.name.toLowerCase().includes(q)
    )
  }, [agencySearch, TOP_AGENCIES, ALL_AGENCIES])

  const toggleSet = (set, value) => {
    const next = new Set(set)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    return next
  }

  const activeCount = useMemo(() => {
    let n = 0
    if (yearFrom) n += 1
    if (yearTo) n += 1
    n += selectedAgencies.size
    n += status.size
    return n
  }, [yearFrom, yearTo, selectedAgencies, status])

  const runSearch = async () => {
    const firstAgency = Array.from(selectedAgencies)[0] || ''
    const data = await searchDockets(query, docType, firstAgency)
    setResults(data)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    runSearch()
  }

  const clearAdvanced = () => {
    setYearFrom('')
    setYearTo('')
    setAgencySearch('')
    setSelectedAgencies(new Set())
    setStatus(new Set())
  }

  const applyAdvanced = () => {
    const first = Array.from(selectedAgencies)[0] || ''
    setAgency(first)
  }

  const advancedPayload = useMemo(
    () => ({
      yearFrom,
      yearTo,
      agencies: Array.from(selectedAgencies),
      status: Array.from(status),
    }),
    [yearFrom, yearTo, selectedAgencies, status]
  )

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">Mirrulations</div>
        <button className="btn btn-primary" type="button">Log Out</button>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <button
            className="advHeader"
            onClick={() => setAdvOpen((v) => !v)}
            aria-expanded={advOpen}
            type="button"
          >
            <div className="advHeaderText">
              <div className="advTitle">Advanced Search</div>
              <div className="advSub">Filters are the fastest way to narrow results.</div>
            </div>
            <div className="advHeaderRight">
              <span className="pill">{activeCount} active</span>
              <span className="chev" aria-hidden="true">{advOpen ? '▾' : '▸'}</span>
            </div>
          </button>

          {advOpen && (
            <div className="advBody">
              <section className="section">
                <h3>Date Range</h3>

                <div className="chipRow">
                  <button type="button" className="chip" onClick={() => { setYearFrom('2021'); setYearTo('2023') }}>
                    2021–2023
                  </button>
                  <button type="button" className="chip" onClick={() => { setYearFrom('2024'); setYearTo('2024') }}>
                    2024
                  </button>
                  <button type="button" className="chip" onClick={() => { setYearFrom(''); setYearTo('') }}>
                    All time
                  </button>
                </div>

                <div className="row">
                  <div className="field">
                    <div className="label">From (year)</div>
                    <input value={yearFrom} onChange={(e) => setYearFrom(e.target.value)} placeholder="e.g. 2021" />
                  </div>
                  <div className="field">
                    <div className="label">To (year)</div>
                    <input value={yearTo} onChange={(e) => setYearTo(e.target.value)} placeholder="e.g. 2023" />
                  </div>
                </div>
              </section>

              <CollapsibleSection
                title="Agency"
                defaultOpen
                right={<span className="pill">{agencySearch.trim() ? "search" : "top"}</span>}
            >
                <input
                    value={agencySearch}
                    onChange={(e) => setAgencySearch(e.target.value)}
                    placeholder="Search agencies…"
                />

                <div className="metaRow">
                    <span>
                        {agencySearch.trim()
                        ? `Results for “${agencySearch.trim()}”`
                        : "Showing top agencies"}
                    </span>
                    <span className="pill">{agenciesToShow.length}</span>
                </div>

                <div className="agencyListStatic">
                    {agenciesToShow
                    .slice(0, agencySearch.trim() ? 8 : 6) // cap results so it stays tidy
                    .map((a) => (
                        <label key={a.code} className="check">
                            <input
                                type="checkbox"
                                checked={selectedAgencies.has(a.code)}
                                onChange={() =>
                                    setSelectedAgencies((prev) => {
                                      if (prev.has(a.code)) {
                                        return new Set() // uncheck if already selected
                                      }
                                      return new Set([a.code]) // replace with only this agency
                                    })
                                  }
                            />
                            <span>{a.code} — {a.name}</span>
                        </label>
                    ))}
                </div>

                {agencySearch.trim() && agenciesToShow.length > 8 && (
                    <div className="hintText">
                        Showing top 8 matches. (Demo behavior)
                    </div>
                )}

                {/* Future placeholder for your “agency categories” */}
                <div className="futureNote">
                    Future: agency category dropdown (TBD categories)
                </div>
            </CollapsibleSection>

              <section className="section">
                <h3>Document Type</h3>
                {["Proposed Rule", "Final Rule", "Notice"].map((t) => (
                <label key={t} className="check">
                    <input
                        type="checkbox"
                        checked={docType === t}
                        onChange={() => setDocType((prev) => (prev === t ? "" : t))}
                    />
                    <span>{t}</span>
                </label>
                ))}
            </section>

              <section className="section">
                <h3>Status</h3>

                {['Open', 'Closed', 'Pending'].map((s) => (
                  <label key={s} className="check">
                    <input
                      type="checkbox"
                      checked={status.has(s)}
                      onChange={() => setStatus((prev) => toggleSet(prev, s))}
                    />
                    <span>{s}</span>
                  </label>
                ))}
              </section>

              <div className="actions">
                <button type="button" className="btn btn-ghost" onClick={clearAdvanced}>
                  Clear
                </button>
                <button type="button" className="btn btn-primary btn-apply" onClick={applyAdvanced}>
                  Apply
                </button>
              </div>
            </div>
          )}
        </aside>

        <main className="main">
          <h1 className="title">Mirrulations Explorer</h1>

          
        <form className="searchBox" onSubmit={handleSubmit}>
            <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search query"
            />
            <button type="submit" className="btn btn-primary">Search</button>
        </form>

          <div className="demoBox">
            <div className="demoTitle">Advanced filters (demo payload)</div>
            <pre>{JSON.stringify(advancedPayload, null, 2)}</pre>
          </div>

          <div className="demoBox">
            <div className="demoTitle">Search results (API response)</div>
            <pre>{JSON.stringify(results, null, 2)}</pre>
          </div>
        </main>
      </div>
    </div>
  )
}