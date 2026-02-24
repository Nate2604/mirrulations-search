import { useState } from 'react'
import './index.css'

export default function App() {
    const [query, setQuery] = useState('')
    const [filter, setFilter] = useState('')
    const [results, setResults] = useState([])

    const runSearch = async () => {
        const res = await fetch(
            `/search/?str=${encodeURIComponent(query)}&filter=${encodeURIComponent(filter)}`
        )
        setResults(await res.json())

    }

    return (
        <div className="container">
            <h1>Mirrulations Explorer</h1>
            <div className = "search-box">
                <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search query"/>
                <select value={filter} onChange={e => setFilter(e.target.value)} placeholder="Filter (optional)">
                    <option value=""> All</option>
                    <option value="Proposed Rule">Proposed Rule</option>
                    <option value="Final Rule">Final Rule</option>
                    <option value="Notice">Notice</option>
                </select>
                <button onClick={runSearch}>Search</button>
            </div>

            <pre id = "output">{JSON.stringify(results, null, 2)}</pre>

        </div>
    )
}