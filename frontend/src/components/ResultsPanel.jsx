export default function ResultsPanel({ advancedPayload, results }) {
  return (
    <>
      <div className="demoBox">
        <div className="demoTitle">Advanced filters</div>
        <pre>{JSON.stringify(advancedPayload, null, 2)}</pre>
      </div>

      <div className="demoBox">
        <div className="demoTitle">Search results</div>
        <pre>{JSON.stringify(results, null, 2)}</pre>
      </div>
    </>
  );
}