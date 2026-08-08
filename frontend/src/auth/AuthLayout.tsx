import type { ReactNode } from 'react'

type Props = { title: string; subtitle: string; children: ReactNode }

export function AuthLayout({ title, subtitle, children }: Props) {
  return (
    <main className="min-h-screen bg-[#fffaf7] p-4 text-[#281320] sm:p-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-5xl overflow-hidden rounded-[2rem] border border-[#efdeda] bg-white shadow-2xl shadow-[#36102d]/10 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="auth-panel flex flex-col justify-between p-8 text-white sm:p-12">
          <a className="text-3xl font-bold" href="/">
            <span className="text-[#ff5c52]" aria-hidden="true">
              ♥
            </span>{' '}
            matcha
          </a>
          <div>
            <p className="text-sm font-semibold tracking-[0.2em] text-[#ffb4ae] uppercase">
              Rencontres authentiques
            </p>
            <h1 className="mt-4 text-4xl leading-tight font-bold">
              Des connexions qui ont du sens.
            </h1>
            <ul className="mt-8 space-y-4 text-sm text-[#eadde7]">
              <li>✓ Profils vérifiés et compatibilité mutuelle</li>
              <li>✓ Localisation approximative, jamais vos coordonnées</li>
              <li>✓ Discussion après un like réciproque</li>
            </ul>
          </div>
          <p className="text-xs text-[#cdbbc8]">
            18+ · Matcha est réservé aux personnes majeures.
          </p>
        </section>
        <section className="flex items-center justify-center p-7 sm:p-12">
          <div className="w-full max-w-md">
            <p className="text-sm font-semibold text-[#ff5149]">
              Bienvenue sur Matcha
            </p>
            <h2 className="mt-2 text-3xl font-bold text-[#35102d]">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-[#755f6d]">{subtitle}</p>
            <div className="mt-8">{children}</div>
          </div>
        </section>
      </div>
    </main>
  )
}

export const fieldClass =
  'mt-2 w-full rounded-xl border border-[#dfd1d7] bg-white px-4 py-3 text-sm outline-none transition focus:border-[#ff5149] focus:ring-4 focus:ring-[#ff5149]/10'
export const buttonClass =
  'w-full rounded-xl bg-[#ff5149] px-5 py-3 font-semibold text-white transition hover:bg-[#e9433c] disabled:cursor-not-allowed disabled:opacity-60'
