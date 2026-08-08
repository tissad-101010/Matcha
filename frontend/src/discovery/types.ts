import type { PhotoSummary, Tag } from '../onboarding/types'

export type ProfileCard = {
  id: string
  first_name: string
  age: number
  main_photo: PhotoSummary | null
  tags: Tag[]
  location: {
    city: string
    district: string | null
    distance_km: number | null
    same_zone: boolean
  }
  popularity: number
  presence: { online: boolean; last_seen_at: string | null }
  common_tags: number
}
