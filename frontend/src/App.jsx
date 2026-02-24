import { useState } from 'react'
import './styles/app.css'
import { searchDockets } from './api/searchApi'

export default function App() {
    const [query, setQuery] = useState('')
    const [filter, setFilter] = useState('')
    const [results, setResults] = useState([])
    const [agency, setAgency] = useState('')

    const runSearch = async () => {
        const data = await searchDockets(query, filter, agency)
        setResults(data)

    }

    const handleSubmit = (event) => {
        event.preventDefault()
        runSearch()
    }

    return (
        <div className="container">
            <h1>Mirrulations Explorer</h1>
            <form className="search-box" onSubmit={handleSubmit}>
                <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search query"/>
                <select value={filter} onChange={e => setFilter(e.target.value)} placeholder="Filter (optional)">
                    <option value=""> All</option>
                    <option value="Proposed Rule">Proposed Rule</option>
                    <option value="Final Rule">Final Rule</option>
                    <option value="Notice">Notice</option>
                </select>
                <select value={agency} onChange={e => setAgency(e.target.value)}>
                    <option value="">All Agencies</option>
                    <option value="CMS">CMS</option>
                    <option value="EPA">EPA</option>
                    <option value="HHS">HHS</option>
                    <option value="FDA">FDA</option>
                </select>
                <button type="submit">Search</button>
            </form>

            <pre id = "output">{JSON.stringify(results, null, 2)}</pre>

        </div>
    )
}