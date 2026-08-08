export function StatusMessage({
  message,
  success = false,
}: {
  message?: string
  success?: boolean
}) {
  if (!message) return null
  return (
    <p
      role={success ? 'status' : 'alert'}
      className={`rounded-xl p-3 text-sm ${success ? 'bg-[#ddf8ee] text-[#176b50]' : 'bg-[#fff0ef] text-[#a52e29]'}`}
    >
      {message}
    </p>
  )
}
