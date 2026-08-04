import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { App } from './App'

describe('App', () => {
  it('renders the accessible Matcha application shell', () => {
    render(<App />)

    expect(
      screen.getByRole('navigation', { name: 'Navigation principale' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Des connexions qui ont du sens.' }),
    ).toBeVisible()
    expect(screen.getByRole('button', { name: 'Se connecter' })).toBeEnabled()
    expect(
      screen.getByText(/n’affiche jamais votre position exacte/i),
    ).toBeVisible()
  })
})
