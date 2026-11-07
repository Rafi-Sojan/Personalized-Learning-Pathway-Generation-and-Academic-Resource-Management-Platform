import { lazy, Suspense, useState } from 'react'
import { BookOpen, BrainCircuit, ChevronRight, CircleUserRound, Compass, FileText, Home, Library, Menu, Route, Settings, ShieldCheck, X } from 'lucide-react'
import { BrowserRouter, Link, Navigate, Route as AppRoute, Routes, useLocation } from 'react-router-dom'
const Dashboard = lazy(() => import('./pages/Dashboard').then((module) => ({ default: module.Dashboard })))
const Courses = lazy(() => import('./pages/Courses').then((module) => ({ default: module.Courses })))
const ConceptMap = lazy(() => import('./pages/ConceptMap').then((module) => ({ default: module.ConceptMap })))
const StudyRoadmap = lazy(() => import('./pages/StudyRoadmap').then((module) => ({ default: module.StudyRoadmap })))
const SyllabusSources = lazy(() => import('./pages/SyllabusSources').then((module) => ({ default: module.SyllabusSources })))
const Login = lazy(() => import('./pages/Login').then((module) => ({ default: module.Login })))
const Account = lazy(() => import('./pages/Account').then((module) => ({ default: module.Account })))
const Exams = lazy(() => import('./pages/Exams').then((module) => ({ default: module.Exams })))
const Admin = lazy(() => import('./pages/Admin').then((module) => ({ default: module.Admin })))
const RvceCatalog = lazy(() => import('./pages/RvceCatalog').then((module) => ({ default: module.RvceCatalog })))
import './styles.css'

type Page = 'dashboard' | 'courses' | 'concepts' | 'roadmap' | 'syllabus' | 'account' | 'exams' | 'admin' | 'rvce'
const navigation: { id: Page; label: string; icon: typeof Home }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Home }, { id: 'courses', label: 'My subjects', icon: BookOpen }, { id: 'rvce', label: 'RVCE syllabus', icon: BookOpen }, { id: 'syllabus', label: 'Syllabus copies', icon: Library }, { id: 'concepts', label: 'Concept map', icon: BrainCircuit }, { id: 'roadmap', label: 'Study roadmap', icon: Route }, { id: 'exams', label: 'Question frequency', icon: FileText }, { id: 'account', label: 'Account', icon: Settings },
]

/** Show an announced loading state while a lazy route is being downloaded. */
function Loading() { return <main aria-live="polite">Loading…</main> }

/** Render the signed-in navigation shell and route table for the learner workspace. */
function AppShell() {
  const location = useLocation(); const [open, setOpen] = useState(false)
  const page = (location.pathname.replace('/', '') || 'dashboard') as Page
  const storedUser = localStorage.getItem('user'); const user = storedUser ? JSON.parse(storedUser) as { role?: string; name?: string } : {}
  const role = user.role
  const initials = (user.name ?? 'Learner').split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
  const visibleNavigation = role === 'admin' ? [...navigation, { id: 'admin' as Page, label: 'Administration', icon: ShieldCheck }] : navigation
  return <div className="app-shell"><aside className={open ? 'sidebar open' : 'sidebar'}><div className="brand"><div className="brand-mark"><Compass size={20} /></div><span>pathway<span className="brand-dot">.</span></span><button aria-label="Close navigation" className="close-menu" type="button" onClick={() => setOpen(false)}><X size={18} /></button></div><div className="workspace-label">MY WORKSPACE</div><nav aria-label="Primary navigation">{visibleNavigation.map(({ id, label, icon: Icon }) => <Link className={page === id ? 'nav-item active' : 'nav-item'} to={`/${id === 'dashboard' ? '' : id}`} onClick={() => setOpen(false)} key={id}><Icon aria-hidden="true" size={18} /><span>{label}</span>{page === id && <ChevronRight aria-hidden="true" size={15} />}</Link>)}</nav><div className="sidebar-bottom"><Link className="profile" to="/account"><CircleUserRound aria-hidden="true" size={28} /><span><strong>{user.name ?? 'Account'}</strong><small>Privacy and sign out</small></span></Link></div></aside><div className="content"><header className="topbar"><button aria-label="Open navigation" className="menu-button" type="button" onClick={() => setOpen(true)}><Menu aria-hidden="true" size={21} /></button><div className="breadcrumb"><span>Workspace</span><ChevronRight aria-hidden="true" size={14} /><strong>{visibleNavigation.find((item) => item.id === page)?.label}</strong></div><div className="top-actions"><Link aria-label="Open account" className="avatar" to="/account">{initials}</Link></div></header><Suspense fallback={<Loading />}><Routes><AppRoute path="/login" element={<Navigate to="/" replace />} /><AppRoute path="/" element={<Dashboard />} /><AppRoute path="/dashboard" element={<Dashboard />} /><AppRoute path="/courses" element={<Courses />} /><AppRoute path="/rvce" element={<RvceCatalog />} /><AppRoute path="/syllabus" element={<SyllabusSources />} /><AppRoute path="/resources" element={<Navigate to="/syllabus" replace />} /><AppRoute path="/concepts" element={<ConceptMap />} /><AppRoute path="/roadmap" element={<StudyRoadmap />} /><AppRoute path="/quizzes" element={<Navigate to="/" replace />} /><AppRoute path="/progress" element={<Navigate to="/" replace />} /><AppRoute path="/account" element={<Account />} /><AppRoute path="/exams" element={<Exams />} /><AppRoute path="/admin" element={<Admin />} /></Routes></Suspense></div></div>
}

/** Choose between the authenticated workspace and the login route. */
export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem('access_token')))
  return <BrowserRouter><Suspense fallback={<Loading />}>{authenticated ? <AppShell /> : <Routes><AppRoute path="/login" element={<Login onSuccess={() => setAuthenticated(true)} />} /><AppRoute path="*" element={<Navigate to="/login" replace />} /></Routes>}</Suspense></BrowserRouter>
}
