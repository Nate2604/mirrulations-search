export default function SearchBar({ query, setQuery, onSubmit }) {
  return (
    <form className="searchBox" onSubmit={onSubmit}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search query"
      />
      <button type="submit" className="btn btn-primary">
        Search
      </button>
    </form>
  );
}