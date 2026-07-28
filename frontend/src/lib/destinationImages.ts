// Fetches a real, location-accurate photo for each destination from the
// Wikipedia (Wikimedia) API. This replaces the discontinued source.unsplash.com
// endpoint, which now returns 503 for every request.
//
// The MediaWiki "pageimages" action generates and caches a thumbnail at the
// requested size server-side, so the returned upload.wikimedia.org URL loads
// reliably (unlike arbitrary on-demand thumbnail widths, which Wikimedia blocks
// for hotlinkers). CORS is enabled via origin=*.

// Destination -> Wikipedia article title
const wikiTitles: Record<string, string> = {
  Sigiriya: 'Sigiriya',
  Ella: 'Ella, Sri Lanka',
  'Galle Fort': 'Galle Fort',
  Kandy: 'Kandy',
  'Nuwara Eliya': 'Nuwara Eliya',
  Mirissa: 'Mirissa',
  Unawatuna: 'Unawatuna',
  Bentota: 'Bentota',
  'Arugam Bay': 'Arugam Bay',
  Trincomalee: 'Trincomalee',
  Anuradhapura: 'Anuradhapura',
  Polonnaruwa: 'Polonnaruwa',
  Dambulla: 'Dambulla cave temple',
  Yala: 'Yala National Park',
  Pinnawala: 'Pinnawala Elephant Orphanage',
  'Adams Peak': "Adam's Peak",
  'Horton Plains': 'Horton Plains National Park',
  Jaffna: 'Jaffna',
  Colombo: 'Colombo',
  Negombo: 'Negombo',
}

// Cache in-flight and resolved lookups so each destination is fetched once.
const cache = new Map<string, Promise<string | null>>()

async function fetchImageUrl(title: string, size: number): Promise<string | null> {
  const params = new URLSearchParams({
    action: 'query',
    titles: title,
    prop: 'pageimages',
    piprop: 'thumbnail',
    pithumbsize: String(size),
    format: 'json',
    origin: '*',
  })
  const res = await fetch(`https://en.wikipedia.org/w/api.php?${params.toString()}`)
  if (!res.ok) throw new Error(`Wikipedia API ${res.status}`)
  const data = await res.json()
  const pages = data?.query?.pages
  if (!pages) return null
  const first = Object.values(pages)[0] as { thumbnail?: { source?: string } }
  return first?.thumbnail?.source ?? null
}

export function getDestinationImageUrl(destination: string, size = 800): Promise<string | null> {
  const title = wikiTitles[destination]
  if (!title) return Promise.resolve(null)

  // Round the size up to a small set of buckets so we reuse cached thumbnails.
  const bucket = size <= 500 ? 500 : size <= 800 ? 800 : 1200
  const key = `${destination}:${bucket}`

  const existing = cache.get(key)
  if (existing) return existing

  const promise = fetchImageUrl(title, bucket).catch(() => null)
  cache.set(key, promise)
  return promise
}
