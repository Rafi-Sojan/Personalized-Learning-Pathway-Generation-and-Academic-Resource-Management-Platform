import { expect, test } from '@playwright/test'

test('login controls are keyboard and label accessible', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible()
  await expect(page.getByLabel('Email')).toBeEditable()
  await expect(page.getByLabel('Password')).toBeEditable()
  await expect(page.getByRole('button', { name: /sign in/i })).toBeEnabled()
})
