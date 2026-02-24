import { useState } from 'react'
import './styles/app.css'
import { searchDockets } from './api/searchApi'

export default function App() {
    const [query, setQuery] = useState('')
    const [filter, setFilter] = useState('')
    const [results, setResults] = useState([])

    const runSearch = async () => {
        const data = await searchDockets(query, filter)
        setResults(data)

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