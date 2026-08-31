import { type ReactNode, type SyntheticEvent, useEffect, useState } from 'react'

import { buttonClass, fieldClass } from '../auth/AuthLayout'
import { errorMessage, requestJson, uploadFile } from '../auth/api'
import { StatusMessage } from '../auth/StatusMessage'
import { navigate } from '../navigation'
import type {
  Gender,
  LocationSuggestion,
  PhotoSummary,
  PrivateProfile,
  Tag,
} from './types'

const genders: Array<[Gender, string]> = [
  ['man', 'Homme'],
  ['woman', 'Femme'],
  ['non_binary', 'Non-binaire'],
]

type LoadedData = {
  profile: PrivateProfile
  tags: Tag[]
  locations: LocationSuggestion[]
  csrfToken: string
  policyVersion: string
}

export function OnboardingPage() {
  const [loaded, setLoaded] = useState<LoadedData | null>(null)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [photos, setPhotos] = useState<PhotoSummary[]>([])
  const [photoBusy, setPhotoBusy] = useState(false)
  const [gpsBusy, setGpsBusy] = useState(false)

  useEffect(() => {
    void loadOnboarding()
      .then((data) => {
        setLoaded(data)
        setPhotos(data.profile.photos)
      })
      .catch((reason: unknown) => {
        setError(errorMessage(reason))
      })
  }, [])

  async function submit(event: SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    event.preventDefault()
    if (!loaded) return
    const form = new FormData(event.currentTarget)
    const desiredGenders = form.getAll('desired_genders') as Gender[]
    const tagIds = form.getAll('tag_ids') as string[]
    const consentConfirmed = form.get('preferences_consent') === 'on'
    setSaving(true)
    setError('')
    try {
      await requestJson(
        '/me/profile',
        'PATCH',
        {
          first_name: form.get('first_name'),
          last_name: form.get('last_name'),
          birth_date: form.get('birth_date'),
          gender: form.get('gender'),
          bio: form.get('bio'),
        },
        loaded.csrfToken,
      )
      if (!consentConfirmed) {
        throw new Error(
          'Le consentement aux préférences est nécessaire pour activer le matching.',
        )
      }
      await requestJson(
        '/me/consents/preferences',
        'PUT',
        {
          confirmed: true,
          policy_version: loaded.policyVersion,
        },
        loaded.csrfToken,
      )
      await requestJson(
        '/me/preferences',
        'PUT',
        {
          desired_genders: desiredGenders,
        },
        loaded.csrfToken,
      )
      await requestJson(
        '/me/tags',
        'PUT',
        { tag_ids: tagIds },
        loaded.csrfToken,
      )
      await requestJson(
        '/me/location/manual',
        'PUT',
        {
          catalog_location_id: form.get('catalog_location_id'),
        },
        loaded.csrfToken,
      )
      navigate('/discover')
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setSaving(false)
    }
  }

  async function addPhoto(file: File | undefined) {
    if (!loaded || !file) return
    setPhotoBusy(true)
    setError('')
    try {
      const response = await uploadFile<{ data: PhotoSummary }>(
        '/me/photos',
        file,
        loaded.csrfToken,
      )
      setPhotos((current) => [...current, response.data])
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setPhotoBusy(false)
    }
  }

  async function makeMain(photoId: string) {
    if (!loaded) return
    setPhotoBusy(true)
    try {
      const response = await requestJson<{ data: PhotoSummary[] }>(
        `/me/photos/${photoId}`,
        'PATCH',
        { is_main: true },
        loaded.csrfToken,
      )
      setPhotos(response.data)
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setPhotoBusy(false)
    }
  }

  async function deletePhoto(photoId: string) {
    if (!loaded) return
    setPhotoBusy(true)
    try {
      await requestJson(
        `/me/photos/${photoId}`,
        'DELETE',
        undefined,
        loaded.csrfToken,
      )
      setPhotos((current) => {
        const remaining = current.filter((photo) => photo.id !== photoId)
        const first = remaining[0]
        if (first && !remaining.some((photo) => photo.is_main)) {
          remaining[0] = { ...first, is_main: true }
        }
        return remaining.map((photo, index) => ({
          ...photo,
          position: index + 1,
        }))
      })
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setPhotoBusy(false)
    }
  }

  async function requestGpsLocation() {
    if (!loaded) return
    const geolocation = Reflect.get(navigator, 'geolocation') as
      Geolocation | undefined
    if (!geolocation) {
      setError(
        'La géolocalisation est indisponible. Choisissez une ville manuellement.',
      )
      return
    }
    setGpsBusy(true)
    setError('')
    try {
      await requestJson(
        '/me/consents/location',
        'PUT',
        { confirmed: true, policy_version: loaded.policyVersion },
        loaded.csrfToken,
      )
      const position = await currentPosition(geolocation)
      const response = await requestJson<{ data: PrivateProfile['location'] }>(
        '/me/location/gps',
        'PUT',
        {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        },
        loaded.csrfToken,
      )
      setLoaded({
        ...loaded,
        profile: {
          ...loaded.profile,
          location: response.data,
          consents: replaceConsent(
            loaded.profile.consents,
            'gps_location',
            true,
            loaded.policyVersion,
          ),
        },
      })
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setGpsBusy(false)
    }
  }

  async function withdrawGpsConsent() {
    if (!loaded) return
    setGpsBusy(true)
    setError('')
    try {
      await requestJson(
        '/me/consents/location',
        'DELETE',
        undefined,
        loaded.csrfToken,
      )
      setLoaded({
        ...loaded,
        profile: {
          ...loaded.profile,
          location:
            loaded.profile.location?.source === 'gps_reduced'
              ? null
              : loaded.profile.location,
          consents: replaceConsent(
            loaded.profile.consents,
            'gps_location',
            false,
            loaded.policyVersion,
          ),
        },
      })
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setGpsBusy(false)
    }
  }

  if (!loaded) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#fffaf7] p-6 text-[#35102d]">
        <div className="text-center">
          <p className="text-2xl font-bold">matcha</p>
          <p className="mt-3" role="status">
            {error || 'Chargement de votre profil…'}
          </p>
          {error && (
            <button
              className="mt-5 font-semibold text-[#d43d37]"
              onClick={() => {
                navigate('/')
              }}
            >
              Se reconnecter
            </button>
          )}
        </div>
      </main>
    )
  }

  const consentActive = loaded.profile.consents.some(
    (consent) => consent.purpose === 'matching_preferences' && consent.granted,
  )
  const gpsConsentActive = loaded.profile.consents.some(
    (consent) => consent.purpose === 'gps_location' && consent.granted,
  )
  return (
    <main className="min-h-screen bg-[#fffaf7] px-4 py-8 text-[#281320] sm:px-8">
      <form
        className="mx-auto max-w-5xl"
        onSubmit={(event) => void submit(event)}
      >
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-2xl font-bold text-[#35102d]">♥ matcha</p>
            <p className="mt-1 text-sm text-[#755f6d]">
              Complétez les informations obligatoires pour découvrir des profils
              compatibles.
            </p>
          </div>
          <p className="rounded-full bg-white px-4 py-2 text-sm shadow-sm">
            Photos facultatives · 0 à 5
          </p>
        </header>
        <StatusMessage message={error} />
        {loaded.profile.missing_profile_fields.length > 0 && (
          <div
            className="mt-5 rounded-xl border border-[#f0c7bf] bg-[#fff1ed] p-4 text-sm"
            role="status"
          >
            <p className="font-semibold">
              Informations requises avant le matching :
            </p>
            <ul className="mt-2 list-inside list-disc">
              {loaded.profile.missing_profile_fields.map((field) => (
                <li key={field}>{missingFieldLabel(field)}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <OnboardingSection number="1" title="Votre profil">
            <div className="grid gap-4 sm:grid-cols-2">
              <TextField
                name="first_name"
                label="Prénom"
                value={loaded.profile.first_name}
              />
              <TextField
                name="last_name"
                label="Nom"
                value={loaded.profile.last_name}
              />
            </div>
            <label className="block text-sm font-medium">
              Date de naissance
              <input
                className={fieldClass}
                name="birth_date"
                type="date"
                defaultValue={loaded.profile.birth_date}
                required
              />
            </label>
            <label className="block text-sm font-medium">
              Genre
              <select
                className={fieldClass}
                name="gender"
                defaultValue={loaded.profile.gender ?? ''}
                required
              >
                <option value="" disabled>
                  Choisir
                </option>
                {genders.map(([value, label]) => (
                  <option value={value} key={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-medium">
              Biographie
              <textarea
                className={`${fieldClass} min-h-28`}
                name="bio"
                maxLength={1000}
                defaultValue={loaded.profile.bio ?? ''}
                required
              />
            </label>
          </OnboardingSection>
          <OnboardingSection number="2" title="Préférences et consentement">
            <p className="text-sm leading-6 text-[#755f6d]">
              Ces données servent uniquement à calculer une compatibilité
              mutuelle. Sans consentement, la découverte et le matching restent
              suspendus.
            </p>
            <fieldset>
              <legend className="text-sm font-semibold">
                Genres recherchés
              </legend>
              <div className="mt-3 flex flex-wrap gap-2">
                {genders.map(([value, label]) => (
                  <Choice
                    key={value}
                    name="desired_genders"
                    value={value}
                    label={label}
                    checked={loaded.profile.desired_genders.includes(value)}
                  />
                ))}
              </div>
              <p className="mt-2 text-xs text-[#755f6d]">
                Aucun choix signifie tous les genres.
              </p>
            </fieldset>
            <label className="flex gap-3 rounded-xl border border-[#efdeda] bg-[#fffaf7] p-4 text-sm">
              <input
                name="preferences_consent"
                type="checkbox"
                defaultChecked={consentActive}
                required
              />
              <span>
                Je consens explicitement au traitement de mes préférences pour
                le matching. Consentement retirable à tout moment.
              </span>
            </label>
          </OnboardingSection>
          <OnboardingSection number="3" title="Centres d’intérêt">
            <p className="text-sm text-[#755f6d]">
              Choisissez entre 1 et 10 tags réutilisables.
            </p>
            <div className="flex flex-wrap gap-2">
              {loaded.tags.map((tag) => (
                <Choice
                  key={tag.id}
                  name="tag_ids"
                  value={tag.id}
                  label={tag.name}
                  checked={loaded.profile.tags.some(
                    (selected) => selected.id === tag.id,
                  )}
                />
              ))}
            </div>
          </OnboardingSection>
          <OnboardingSection number="4" title="Localisation approximative">
            <p className="text-sm leading-6 text-[#755f6d]">
              Choisissez une ville du catalogue local. Aucune coordonnée exacte
              n’est affichée ni conservée.
            </p>
            <label className="block text-sm font-medium">
              Ville ou quartier
              <select
                className={fieldClass}
                name="catalog_location_id"
                defaultValue={
                  loaded.profile.location?.catalog_location_id ?? ''
                }
                required
              >
                <option value="" disabled>
                  Choisir une localisation
                </option>
                {loaded.locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="space-y-3 rounded-xl bg-[#f7f0f4] p-4 text-sm text-[#755f6d]">
              <p>
                Le GPS est facultatif et n’est demandé qu’après votre action.
                Les coordonnées exactes sont immédiatement remplacées par une
                zone approximative.
              </p>
              {gpsConsentActive ? (
                <button
                  type="button"
                  className="font-semibold text-[#d43d37]"
                  disabled={gpsBusy}
                  onClick={() => void withdrawGpsConsent()}
                >
                  Retirer mon consentement GPS
                </button>
              ) : (
                <button
                  type="button"
                  className="font-semibold text-[#d43d37]"
                  disabled={gpsBusy}
                  onClick={() => void requestGpsLocation()}
                >
                  {gpsBusy
                    ? 'Localisation en cours…'
                    : 'Utiliser ma position approximative'}
                </button>
              )}
              <p>
                La saisie manuelle reste obligatoire si le GPS est refusé ou
                indisponible.
              </p>
            </div>
          </OnboardingSection>
          <OnboardingSection number="5" title="Photos facultatives">
            <p className="text-sm leading-6 text-[#755f6d]">
              Ajoutez jusqu’à cinq images JPEG, PNG ou WebP. Elles sont
              nettoyées et stockées dans un espace privé. Vous pourrez compléter
              cette partie plus tard.
            </p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {photos.map((photo) => (
                <article
                  className="overflow-hidden rounded-2xl border border-[#efdeda]"
                  key={photo.id}
                >
                  <img
                    className="aspect-square w-full object-cover"
                    src={photo.url}
                    alt={`Photo ${String(photo.position)}`}
                  />
                  <div className="space-y-2 p-3 text-xs">
                    <p className="font-semibold">
                      {photo.is_main
                        ? 'Photo principale'
                        : `Position ${String(photo.position)}`}
                    </p>
                    {!photo.is_main && (
                      <button
                        type="button"
                        className="block font-semibold text-[#d43d37]"
                        onClick={() => void makeMain(photo.id)}
                      >
                        Définir comme principale
                      </button>
                    )}
                    <button
                      type="button"
                      className="block text-[#755f6d]"
                      disabled={photoBusy}
                      onClick={() => void deletePhoto(photo.id)}
                    >
                      Supprimer
                    </button>
                  </div>
                </article>
              ))}
            </div>
            <label
              className={`block rounded-2xl border border-dashed border-[#d9bdc8] p-5 text-center text-sm font-semibold ${photos.length >= 5 ? 'cursor-not-allowed opacity-50' : 'cursor-pointer text-[#d43d37]'}`}
            >
              {photoBusy ? 'Traitement sécurisé…' : 'Ajouter une photo'}
              <input
                className="sr-only"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                disabled={photoBusy || photos.length >= 5}
                onChange={(event) => {
                  void addPhoto(event.target.files?.[0])
                  event.target.value = ''
                }}
              />
            </label>
          </OnboardingSection>
        </div>
        <div className="mx-auto mt-8 max-w-md">
          <button className={buttonClass} disabled={saving}>
            {saving ? 'Enregistrement…' : 'Enregistrer et découvrir'}
          </button>
        </div>
      </form>
    </main>
  )
}

async function loadOnboarding(): Promise<LoadedData> {
  const session = await requestJson<{ data: { csrf_token: string } }>(
    '/auth/session',
  )
  const [profile, tags, locations, consents] = await Promise.all([
    requestJson<{ data: PrivateProfile }>('/me/profile'),
    requestJson<{ data: Tag[] }>('/tags?limit=20'),
    requestJson<{ data: LocationSuggestion[] }>('/locations?limit=20'),
    requestJson<{ meta: { current_policy_version: string } }>('/me/consents'),
  ])
  return {
    profile: profile.data,
    tags: tags.data,
    locations: locations.data,
    csrfToken: session.data.csrf_token,
    policyVersion: consents.meta.current_policy_version,
  }
}

function currentPosition(geolocation: Geolocation) {
  return new Promise<GeolocationPosition>((resolve, reject) => {
    geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: false,
      timeout: 10_000,
      maximumAge: 60_000,
    })
  })
}

function replaceConsent(
  consents: PrivateProfile['consents'],
  purpose: string,
  granted: boolean,
  policyVersion: string,
) {
  return [
    ...consents.filter((consent) => consent.purpose !== purpose),
    {
      purpose,
      granted,
      policy_version: policyVersion,
      occurred_at: new Date().toISOString(),
    },
  ]
}

function missingFieldLabel(field: string) {
  const labels: Record<string, string> = {
    gender: 'Votre genre',
    bio: 'Une biographie',
    tags: 'Au moins un centre d’intérêt',
    location: 'Une ville ou un quartier',
  }
  return labels[field] ?? field
}

function OnboardingSection({
  number,
  title,
  children,
}: {
  number: string
  title: string
  children: ReactNode
}) {
  return (
    <section className="space-y-5 rounded-3xl border border-[#efdeda] bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="grid size-8 place-items-center rounded-full bg-[#ff5149] text-sm font-bold text-white">
          {number}
        </span>
        <h1 className="text-xl font-bold text-[#35102d]">{title}</h1>
      </div>
      {children}
    </section>
  )
}

function TextField({
  name,
  label,
  value,
}: {
  name: string
  label: string
  value: string
}) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <input className={fieldClass} name={name} defaultValue={value} required />
    </label>
  )
}

function Choice({
  name,
  value,
  label,
  checked,
}: {
  name: string
  value: string
  label: string
  checked: boolean
}) {
  return (
    <label className="cursor-pointer rounded-full border border-[#dfd1d7] px-4 py-2 text-sm has-checked:border-[#ff5149] has-checked:bg-[#fff0ef]">
      <input
        className="sr-only"
        type="checkbox"
        name={name}
        value={value}
        defaultChecked={checked}
      />
      {label}
    </label>
  )
}
