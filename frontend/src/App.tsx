const navigationItems = ['Découvrir', 'Recherche', 'Messages', 'Activité']

export function App() {
  return (
    <div className="min-h-screen bg-[#fffaf7] text-[#281320]">
      <header className="border-b border-[#f1ded7] bg-white">
        <nav
          aria-label="Navigation principale"
          className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4"
        >
          <a className="text-2xl font-bold text-[#3a102d]" href="/">
            matcha <span aria-hidden="true">♥</span>
          </a>
          <ul className="hidden gap-6 md:flex">
            {navigationItems.map((item) => (
              <li key={item}>
                <a
                  className="font-medium hover:text-[#ff5c52]"
                  href={`#${item.toLowerCase()}`}
                >
                  {item}
                </a>
              </li>
            ))}
          </ul>
          <button className="rounded-full bg-[#ff5c52] px-5 py-2 font-semibold text-white">
            Se connecter
          </button>
        </nav>
      </header>

      <main className="mx-auto grid max-w-6xl gap-10 px-5 py-20 md:grid-cols-2 md:items-center">
        <section>
          <p className="mb-3 font-semibold text-[#ff5c52]">
            Rencontres authentiques · 18+
          </p>
          <h1 className="text-5xl leading-tight font-bold text-[#3a102d]">
            Des connexions qui ont du sens.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-[#6f5b67]">
            Découvrez des profils compatibles selon votre zone, vos centres
            d’intérêt et vos préférences de rencontre.
          </p>
          <a
            className="mt-8 inline-block rounded-full bg-[#ff5c52] px-7 py-3 font-semibold text-white"
            href="#inscription"
          >
            Créer mon profil
          </a>
        </section>

        <aside
          aria-label="Fonctionnalités principales"
          className="rounded-3xl border border-[#f1ded7] bg-white p-8 shadow-xl shadow-[#4b1730]/5"
        >
          <h2 className="text-2xl font-bold">Matcha en trois étapes</h2>
          <ol className="mt-6 space-y-5">
            <li>
              1. Complétez votre profil et votre localisation approximative.
            </li>
            <li>
              2. Découvrez des personnes compatibles et partageant vos intérêts.
            </li>
            <li>3. Échangez en temps réel après un like réciproque.</li>
          </ol>
        </aside>
      </main>

      <footer className="border-t border-[#f1ded7] bg-white px-5 py-6 text-center text-sm">
        Matcha respecte vos choix de consentement et n’affiche jamais votre
        position exacte.
      </footer>
    </div>
  )
}
