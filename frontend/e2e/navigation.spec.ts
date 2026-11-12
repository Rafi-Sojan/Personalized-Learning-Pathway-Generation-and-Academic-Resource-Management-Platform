import { expect, test, type Page } from '@playwright/test'

const courseFixture = { id: 'course-1', title: 'Python', code: 'CS101', description: '', progress: 0, concept_count: 1, program_code: 'CS', scheme_year: 2022, semester: 3, origin: 'personal', catalog_course_id: null, syllabus_source_count: 0, syllabus_status: 'not_uploaded' }

/** Prepare an authenticated learner and deterministic syllabus API responses. */
async function prepareSyllabusWorkspace(page: Page) {
  await page.addInitScript(() => { localStorage.setItem('access_token', 'test-token'); localStorage.setItem('user', JSON.stringify({ id: 'student', email: 'student@example.com', name: 'Student', role: 'student' })) })
  await page.route('**/api/v1/courses', (route) => route.fulfill({ json: [courseFixture] }))
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

test('successful login enters the authenticated workspace', async ({ page }) => {
  await page.route('**/api/v1/auth/login', (route) => route.fulfill({ json: { access_token: 'test-token', token_type: 'bearer', user: { id: 'student', email: 'student@example.com', name: 'Student', role: 'student' } } }))
  await page.route('**/api/v1/courses', (route) => route.fulfill({ json: [] }))
  await page.route('**/api/v1/concepts**', (route) => route.fulfill({ json: [] }))
  await page.route('**/api/v1/roadmap/history', (route) => route.fulfill({ json: [] }))
  await page.goto('/login')
  await page.getByLabel(/email/i).fill('student@example.com')
  await page.getByLabel(/password/i).fill('test-password')
  await page.getByRole('button', { name: /sign in/i }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: /good|welcome|dashboard/i })).toBeVisible()
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

  await expect(page).toHaveURL(/\/syllabus(?:\?.*)?$/)

  const url = new URL(page.url())

  expect(url.pathname).toBe('/syllabus')
  expect(url.searchParams.get('course_id')).toBe('course-1')

  await expect(
    page.getByRole('heading', { name: 'Syllabus copies' })
  ).toBeVisible()
})


test('learner can create a branch-scoped personal subject', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('access_token', 'test-token'); localStorage.setItem('user', JSON.stringify({ id: 'student', email: 'student@example.com', name: 'Student', role: 'student' })) })
  let courses = [] as typeof courseFixture[]
  await page.route('**/api/v1/catalog/rvce', (route) => route.fulfill({ json: { program_schemes: [{ code: 'AI', name: 'Artificial Intelligence and Machine Learning', schemes: [2022], aliases: ['AIML'] }], common_first_year_schemes: [2025] } }))
  await page.route('**/api/v1/courses', async (route) => {
    if (route.request().method() === 'POST') {
      const payload = route.request().postDataJSON() as { code: string; title: string; program_code: string; scheme_year: number; semester: number }
      expect(payload).toMatchObject({ code: 'AI253IA', title: 'Deep Learning', program_code: 'AI', scheme_year: 2022, semester: 5 })
      courses = [{ ...courseFixture, id: 'course-ai', code: payload.code, title: payload.title, program_code: payload.program_code, scheme_year: payload.scheme_year, semester: payload.semester }]
      await route.fulfill({ status: 201, json: courses[0] })
      return
    }
    await route.fulfill({ json: courses })
  })

  await page.goto('/courses')
  await page.getByLabel('Semester').selectOption('5')
  await page.getByLabel('Subject code').fill('AI253IA')
  await page.getByLabel('Subject title').fill('Deep Learning')
  await page.getByRole('button', { name: 'Add subject', exact: true }).click()

  await expect(page.getByRole('status')).toContainText('Subject added')
  await expect(page.getByRole('heading', { name: 'Deep Learning' })).toBeVisible()
  await expect(page.getByText('AI · 2022 scheme · Semester 5')).toBeVisible()
})
