export async function searchDockets(query, document_type = '', agency = '') {
    // EncodeURIComponent allows for spaces, special chars, etc
	const response = await fetch(
        `/search/?str=${encodeURIComponent(query)}&document_type=${encodeURIComponent(document_type)}&agency=${encodeURIComponent(agency)}`
    )

	if (!response.ok) {
		throw new Error(`Search request failed: ${response.status}`)
	}

	return response.json()
}

