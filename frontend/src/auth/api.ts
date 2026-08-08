export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly code = 'network_error',
    readonly fields?: Record<string, string>,
  ) {
    super(message)
  }
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(path, 'POST', body)
}

export async function requestJson<T>(
  path: string,
  method = 'GET',
  body?: unknown,
  csrfToken?: string,
): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    method,
    credentials: 'same-origin',
    headers: {
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  const payload: unknown =
    response.status === 204 ? null : await response.json()
  if (!response.ok) {
    if (hasApiError(payload)) {
      throw new ApiRequestError(
        payload.error.message,
        payload.error.code,
        payload.error.fields,
      )
    }
    throw new ApiRequestError('Une erreur est survenue. Réessayez.')
  }
  return payload as T
}

function hasApiError(value: unknown): value is {
  error: { code: string; message: string; fields?: Record<string, string> }
} {
  if (typeof value !== 'object' || value === null || !('error' in value))
    return false
  const error = value.error
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    typeof error.code === 'string' &&
    'message' in error &&
    typeof error.message === 'string'
  )
}

export function errorMessage(reason: unknown) {
  return reason instanceof Error
    ? reason.message
    : 'Une erreur est survenue. Réessayez.'
}
