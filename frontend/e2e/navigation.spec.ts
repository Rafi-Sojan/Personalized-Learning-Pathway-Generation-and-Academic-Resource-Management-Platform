import { expect, test } from '@playwright/test'

test('unauthenticated visitors are directed to login', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
})

test('login screen exposes labeled controls', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByLabel(/email/i)).toBeVisible()
  await expect(page.getByLabel(/password/i)).toBeVisible()
  await expect(page.getByRole('button', { name: /sign in|log in/i })).toBeVisible()
})
