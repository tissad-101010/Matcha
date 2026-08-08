export type Gender = 'man' | 'woman' | 'non_binary'

export type Tag = { id: string; name: string }
export type LocationSuggestion = {
  id: string
  city: string
  district: string | null
  label: string
}

export type PrivateProfile = {
  first_name: string
  last_name: string
  birth_date: string
  gender: Gender | null
  bio: string | null
  desired_genders: Gender[]
  tags: Tag[]
  location: { catalog_location_id: string; city: string } | null
  consents: Array<{ purpose: string; granted: boolean }>
  profile_complete: boolean
  missing_profile_fields: string[]
}
