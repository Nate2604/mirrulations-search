export async function searchDockets(query, filter = '', agency = '') {
    // EncodeURIComponent allows for spaces, special chars, etc
	const response = await fetch(
        `/search/?str=${encodeURIComponent(query)}&filter=${encodeURIComponent(filter)}&agency=${encodeURIComponent(agency)}`
    )

	if (!response.ok) {
		throw new Error(`Search request failed: ${response.status}`)
	}

	return response.json()
}

