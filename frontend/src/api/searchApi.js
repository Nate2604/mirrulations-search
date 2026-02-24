export async function searchDockets(query, filter = '') {
	const response = await fetch(
		`/search/?str=${encodeURIComponent(query)}&filter=${encodeURIComponent(filter)}`
	)

	if (!response.ok) {
		throw new Error(`Search request failed: ${response.status}`)
	}

	return response.json()
}

