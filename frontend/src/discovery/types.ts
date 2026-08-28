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

export type PublicProfile = {
  id: string
  username: string
  first_name: string
  last_name: string
  age: number
  gender: 'man' | 'woman' | 'non_binary'
  desired_genders: Array<'man' | 'woman' | 'non_binary'>
  bio: string
  photos: PhotoSummary[]
  tags: Tag[]
  location: { city: string; district: string | null }
  popularity: number
  presence: { online: boolean; last_seen_at: string | null }
  viewer_state: {
    liked_by_me: boolean
    likes_me: boolean
    matched: boolean
    match_id: string | null
    can_like: boolean
    can_message: boolean
    match_created?: boolean
  }
}
