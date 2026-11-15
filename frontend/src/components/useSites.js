import { useEffect, useState } from 'react'
import { api } from '../api'

let cache = null
/** Standorte der Gruppe (einmal geladen, im Speicher gehalten). */
export function useSites() {
  const [sites, setSites] = useState(cache || [])
  useEffect(() => {
    if (cache) return
    api.get('/sites?limit=50&sort=sort').then((x) => { cache = x.items; setSites(x.items) }).catch(() => {})
  }, [])
  return sites
}
export const siteOptions = (sites) => sites.map((x) => ({ value: x.id, label: x.name }))
