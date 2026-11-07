import { expect, test, type Page } from '@playwright/test'

/** Prepare an authenticated learner and deterministic syllabus API responses. */
async function prepareSyllabusWorkspace(page: Page) {
  await page.addInitScript(() => { localStorage.setItem('access_token', 'test-token'); localStorage.setItem('user', JSON.stringify({ id: 'student', email: 'student@example.com', name: 'Student', role: 'student' })) })
  await page.route('**/api/v1/courses', (route) => route.fulfill({ json: [{ id: 'course-1', title: 'Python', code: 'CS101', description: '', progress: 0, concept_count: 1 }] }))
  await page.route('**/api/v1/syllabus/sources?*', (route) => route.fulfill({ json: [] }))
  await page.route('**/api/v1/syllabus/records?*', (route) => route.fulfill({ json: [] }))
}

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

test('authenticated learner can open the syllabus intake workflow', async ({ page }) => {
  await prepareSyllabusWorkspace(page)
  await page.goto('/syllabus')
  await expect(page.getByRole('heading', { name: 'Syllabus copies' })).toBeVisible()
  await expect(page.getByLabel('PDF copy')).toBeVisible()
})

test('legacy resource route redirects to syllabus copies', async ({ page }) => {
  await prepareSyllabusWorkspace(page)
  await page.goto('/resources')
  await expect(page).toHaveURL(/\/syllabus$/)
  await expect(page.getByRole('heading', { name: 'Syllabus copies' })).toBeVisible()
})
