import { useEffect, useState, useMemo } from "react";
import {
  getCollections,
  createCollection,
  deleteCollection,
  removeDocketFromCollection,
  getDocketsByIds,
} from "../api/collectionsApi";
import "../styles/collections.css";

/** Must match ResultsPanel — overlay search result doc/comment counts onto /dockets rows. */
const DOCKET_METRICS_SESSION_KEY = "mirrulations_docket_metrics_v1";

function readRememberedMetrics() {
  try {
    const raw = sessionStorage.getItem(DOCKET_METRICS_SESSION_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

const ECFR_URL = "https://www.ecfr.gov";
const EMPTY_DOCKET_IDS = [];

export default function Collections() {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedCollectionId, setSelectedCollectionId] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [error, setError] = useState("");
  const [unauthorized, setUnauthorized] = useState(false);
  const [docketDetails, setDocketDetails] = useState({});
  /**
   * modified_desc / modified_asc — last modified
   * title_asc / title_desc — title A–Z / Z–A
   * documents_desc / documents_asc — by documentDenominator (total documents)
   * comments_desc / comments_asc — by commentDenominator (total comments)
   * Counts use documentNumerator/Denominator & commentNumerator/Denominator like ResultsPanel,
   * merged from search in this browser when those dockets were on a results page.
   */
  const [docketSortOrder, setDocketSortOrder] = useState("modified_desc");

  const selectedCollection = collections.find(
    (c) => c.collection_id === selectedCollectionId
  );
  const selectedDocketIds = selectedCollection?.docket_ids ?? EMPTY_DOCKET_IDS;

  const loadCollections = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getCollections();
      setCollections(Array.isArray(data) ? data : []);
    } catch (err) {
      if (err.message === "UNAUTHORIZED") {
        setUnauthorized(true);
      } else {
        setError("Failed to load collections.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCollections();
  }, []);

  useEffect(() => {
    if (collections.length === 0) {
      setSelectedCollectionId(null);
      return;
    }
    const hasSelected = collections.some(
      (collection) => collection.collection_id === selectedCollectionId
    );
    if (!hasSelected) {
      setSelectedCollectionId(collections[0].collection_id);
    }
  }, [collections, selectedCollectionId]);

  useEffect(() => {
    if (!selectedDocketIds.length) return;
    getDocketsByIds(selectedDocketIds).then((results) => {
      const stored = readRememberedMetrics();
      setDocketDetails((prev) => {
        const next = { ...prev };
        results.forEach((d) => {
          const id = d.docket_id;
          const m = stored[id];
          next[id] = {
            ...d,
            documentNumerator: m?.documentNumerator ?? d.documentNumerator ?? 0,
            documentDenominator: m?.documentDenominator ?? d.documentDenominator ?? 0,
            commentNumerator: m?.commentNumerator ?? d.commentNumerator ?? 0,
            commentDenominator: m?.commentDenominator ?? d.commentDenominator ?? 0,
          };
        });
        return next;
      });
    });
  }, [selectedCollectionId, selectedDocketIds]);

  const handleCreate = async (e) => {
    e.preventDefault();
    const trimmedName = newCollectionName.trim();
    if (!trimmedName) return;

    setSubmitting(true);
    setError("");
    try {
      const created = await createCollection(trimmedName);
      const newCollection = {
        collection_id: created.collection_id,
        name: trimmedName,
        docket_ids: [],
      };
      setCollections((prev) => [
        ...prev,
        newCollection,
      ]);
      setSelectedCollectionId(created.collection_id);
      setShowCreateForm(false);
      setNewCollectionName("");
    } catch (err) {
      if (err.message === "UNAUTHORIZED") {
        setUnauthorized(true);
      } else {
        setError("Failed to create collection.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCollection = async (collectionId) => {
    setError("");
    try {
      await deleteCollection(collectionId);
      setCollections((prev) =>
        prev.filter((col) => col.collection_id !== collectionId)
      );
      setEditMode(false);
    } catch (err) {
      if (err.message === "UNAUTHORIZED") {
        setUnauthorized(true);
      } else {
        setError("Failed to delete collection.");
      }
    }
  };

  const handleRemoveDocket = async (collectionId, docketId) => {
    setError("");
    try {
      await removeDocketFromCollection(collectionId, docketId);
      setCollections((prev) =>
        prev.map((col) =>
          col.collection_id === collectionId
            ? {
                ...col,
                docket_ids: (col.docket_ids || []).filter((id) => id !== docketId),
              }
            : col
        )
      );
    } catch (err) {
      if (err.message === "UNAUTHORIZED") {
        setUnauthorized(true);
      } else {
        setError("Failed to remove docket from collection.");
      }
    }
  };

  const sortedDocketIds = useMemo(() => {
    const ids = [...selectedDocketIds];
    const row = (id) => docketDetails[id] ?? {};
    const getTime = (docketId) => {
      const raw = docketDetails[docketId]?.modify_date;
      if (raw == null || raw === "") return null;
      const t = Date.parse(String(raw));
      return Number.isNaN(t) ? null : t;
    };
    const getTitle = (docketId) => {
      const t = docketDetails[docketId]?.docket_title;
      return (t != null ? String(t) : "").trim();
    };
    const docTotal = (id) => Number(row(id).documentDenominator ?? 0);
    const comTotal = (id) => Number(row(id).commentDenominator ?? 0);
    ids.sort((a, b) => {
      if (docketSortOrder === "documents_desc" || docketSortOrder === "documents_asc") {
        const cmp = docTotal(b) - docTotal(a);
        if (cmp !== 0) {
          return docketSortOrder === "documents_desc" ? cmp : -cmp;
        }
        return String(a).localeCompare(String(b));
      }
      if (docketSortOrder === "comments_desc" || docketSortOrder === "comments_asc") {
        const cmp = comTotal(b) - comTotal(a);
        if (cmp !== 0) {
          return docketSortOrder === "comments_desc" ? cmp : -cmp;
        }
        return String(a).localeCompare(String(b));
      }
      if (docketSortOrder === "title_asc" || docketSortOrder === "title_desc") {
        const ta = getTitle(a);
        const tb = getTitle(b);
        const cmp = ta.localeCompare(tb, undefined, { sensitivity: "base" });
        if (cmp !== 0) {
          return docketSortOrder === "title_desc" ? -cmp : cmp;
        }
        return String(a).localeCompare(String(b));
      }
      const ta = getTime(a);
      const tb = getTime(b);
      if (ta == null && tb == null) return 0;
      if (ta == null) return 1;
      if (tb == null) return -1;
      const cmp = ta - tb;
      return docketSortOrder === "modified_desc" ? -cmp : cmp;
    });
    return ids;
  }, [selectedDocketIds, docketDetails, docketSortOrder]);

  if (unauthorized) {
    return (
      <section className="collections-page">
        <h1 className="collections-title">My Collections</h1>
        <p>Please <a href="/login">log in</a> to view collections.</p>
      </section>
    );
  }

  const handleDownloadAll = () => {
    if (!selectedCollection) return;
    const lines = [
      `Collection: ${selectedCollection.name}`,
      "",
      ...sortedDocketIds.map((docketId) => docketId),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedCollection.name.replace(/\s+/g, "-").toLowerCase()}-dockets.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="collections-page collections-layout">
      <div className="collections-rail">
        <aside className="collections-sidebar">
        <div className="collections-sidebar-header">
          <div>
            <h2>My Collections</h2>
            <p>All your saved dockets in one place!</p>
          </div>
          <button
            type="button"
            className="collections-plus"
            onClick={() => setShowCreateForm((prev) => !prev)}
          >
            +
          </button>
        </div>

        {showCreateForm && (
          <form className="collections-create-inline" onSubmit={handleCreate}>
            <input
              type="text"
              placeholder="New collection name"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || !newCollectionName.trim()}
            >
              {submitting ? "Creating..." : "Create"}
            </button>
          </form>
        )}

        {loading ? (
          <p className="collections-muted">Loading collections...</p>
        ) : collections.length === 0 ? (
          <p className="collections-muted">No collections yet.</p>
        ) : (
          <div className="collections-nav-list">
            {collections.map((collection) => (
              <button
                key={collection.collection_id}
                type="button"
                className={`collections-nav-item ${
                  selectedCollectionId === collection.collection_id ? "is-active" : ""
                }`}
                onClick={() => {
                  setSelectedCollectionId(collection.collection_id);
                  setEditMode(false);
                }}
              >
                {collection.name}
              </button>
            ))}
          </div>
        )}
        </aside>

        <aside className="collections-sort-sidebar" aria-label="Sort dockets">
          <div className="collections-sort-sidebar-header">
            <h2 className="collections-sort-sidebar-heading">Sort dockets</h2>
            <p className="collections-sort-sidebar-lede">
              Document/comment totals match search when you have opened those dockets on results (this browser).
            </p>
          </div>
          <div className="collections-sort-sidebar-body">
            <div className="collections-sort-section">
              <h3 className="collections-sort-section-label">Documents</h3>
              <p className="collections-sort-section-desc">By documentDenominator (total)</p>
              <div
                className="collections-sort-toggle"
                role="group"
                aria-label="Sort by document total"
              >
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "documents_desc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("documents_desc")}
                >
                  <span className="collections-sort-btn-label">High → low</span>
                  <span className="collections-sort-btn-hint">Most documents first</span>
                </button>
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "documents_asc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("documents_asc")}
                >
                  <span className="collections-sort-btn-label">Low → high</span>
                  <span className="collections-sort-btn-hint">Fewest documents first</span>
                </button>
              </div>
            </div>

            <div className="collections-sort-section">
              <h3 className="collections-sort-section-label">Comments</h3>
              <p className="collections-sort-section-desc">By commentDenominator (total)</p>
              <div
                className="collections-sort-toggle"
                role="group"
                aria-label="Sort by comment total"
              >
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "comments_desc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("comments_desc")}
                >
                  <span className="collections-sort-btn-label">High → low</span>
                  <span className="collections-sort-btn-hint">Most comments first</span>
                </button>
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "comments_asc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("comments_asc")}
                >
                  <span className="collections-sort-btn-label">Low → high</span>
                  <span className="collections-sort-btn-hint">Fewest comments first</span>
                </button>
              </div>
            </div>

            <div className="collections-sort-section">
              <h3 className="collections-sort-section-label">Modified date</h3>
              <div
                className="collections-sort-toggle"
                role="group"
                aria-label="Sort dockets by modified date"
              >
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "modified_desc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("modified_desc")}
                >
                  <span className="collections-sort-btn-label">Newest first</span>
                  <span className="collections-sort-btn-hint">Latest changes</span>
                </button>
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "modified_asc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("modified_asc")}
                >
                  <span className="collections-sort-btn-label">Oldest first</span>
                  <span className="collections-sort-btn-hint">Earliest changes</span>
                </button>
              </div>
            </div>

            <div className="collections-sort-section">
              <h3 className="collections-sort-section-label">Docket title</h3>
              <p className="collections-sort-section-desc">Alphabetical by docket title</p>
              <div
                className="collections-sort-toggle"
                role="group"
                aria-label="Sort dockets by title"
              >
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "title_asc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("title_asc")}
                >
                  <span className="collections-sort-btn-label">A → Z</span>
                  <span className="collections-sort-btn-hint">Ascending</span>
                </button>
                <button
                  type="button"
                  className={`collections-sort-btn ${docketSortOrder === "title_desc" ? "is-selected" : ""}`}
                  onClick={() => setDocketSortOrder("title_desc")}
                >
                  <span className="collections-sort-btn-label">Z → A</span>
                  <span className="collections-sort-btn-hint">Descending</span>
                </button>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <div className="collections-content">
        {error && <p className="collections-error">{error}</p>}

        {!selectedCollection ? (
          <p className="collections-muted">Select or create a collection to continue.</p>
        ) : (
          <>
            <h1 className="collections-title">{selectedCollection.name}</h1>
            <div className="collections-toolbar">
              <p className="collections-summary">
                Showing dockets in "{selectedCollection.name}" • {selectedDocketIds.length}{" "}
                docket{selectedDocketIds.length === 1 ? "" : "s"} found
              </p>
              <div className="collections-actions">
                <button
                  type="button"
                  className="collections-action-btn collections-action-btn-secondary"
                  onClick={() => setEditMode((prev) => !prev)}
                >
                  {editMode ? "Done" : "Edit"}
                </button>
                <button
                  type="button"
                  className="collections-action-btn"
                  onClick={handleDownloadAll}
                  disabled={selectedDocketIds.length === 0}
                >
                  Download All
                </button>
                {editMode && (
                  <button
                    type="button"
                    className="collection-delete"
                    onClick={() => handleDeleteCollection(selectedCollection.collection_id)}
                  >
                    Delete Collection
                  </button>
                )}
              </div>
            </div>

            {selectedDocketIds.length === 0 ? (
              <p className="collections-muted">No dockets in this collection.</p>
            ) : (
              <div className="collection-results">
                {sortedDocketIds.map((docketId) => {
                  const item = docketDetails[docketId];
                  if (!item) return <div key={docketId} className="result-card"><p>Loading...</p></div>;
                  return (
                      <article key={docketId} className="result-card">
                          <h3 className="result-title">{item.docket_title}</h3>
                          <div className="result-meta">
                              <p><strong>Agency:</strong> {item.agency_id}</p>
                              <p><strong>Docket-ID:</strong> {item.docket_id}</p>
                              <p><strong>Docket type:</strong> {item.docket_type}</p>
                              <p>
                                  <strong>CFR:</strong>{" "}
                                  {item.cfrPart && item.cfrPart.length > 0 ? (
                                      item.cfrPart.map((p, idx) => (
                                          <span key={idx}>
                                              <a href={p.link} target="_blank" rel="noopener noreferrer">
                                                  {p.title != null ? `${p.title} Part ${p.part}` : p.part}
                                              </a>
                                              {idx < item.cfrPart.length - 1 && ", "}
                                          </span>
                                      ))
                                  ) : (
                                      <a href={ECFR_URL} target="_blank" rel="noopener noreferrer">None</a>
                                  )}
                              </p>
                              <p><strong>Last modified date:</strong> {item.modify_date}</p>
                              <p>
                                <strong>Documents:</strong> {item.documentNumerator ?? 0}/
                                {item.documentDenominator ?? 0}
                              </p>
                              <p>
                                <strong>Comments:</strong> {item.commentNumerator ?? 0}/
                                {item.commentDenominator ?? 0}
                              </p>
                          </div>
                          {editMode && (
                              <button className="collection-remove-docket"
                                  onClick={() => handleRemoveDocket(selectedCollection.collection_id, docketId)}>
                                  Remove from Collection
                              </button>
                          )}
                      </article>
                  );
              })}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
