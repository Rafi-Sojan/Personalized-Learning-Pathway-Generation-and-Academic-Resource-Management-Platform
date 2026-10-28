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

test('authenticated learner can open the resource intake workflow', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('access_token', 'test-token'); localStorage.setItem('user', JSON.stringify({ id: 'student', email: 'student@example.com', name: 'Student', role: 'student' })) })
  await page.route('**/api/v1/resources*', (route) => route.fulfill({ json: [] }))
  await page.route('**/api/v1/courses', (route) => route.fulfill({ json: [{ id: 'course-1', title: 'Python', code: 'CS101', description: '', progress: 0, concept_count: 1 }] }))
  await page.goto('/resources')
  await expect(page.getByRole('heading', { name: 'Resources' })).toBeVisible()
  await expect(page.getByLabel('PDF file')).toBeVisible()
})
