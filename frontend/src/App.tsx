import { lazy, Suspense, useState } from 'react'
import { BarChart3, BookOpen, BrainCircuit, ChevronRight, CircleUserRound, Compass, Home, Layers3, Library, Menu, Route, Settings, Sparkles, Trophy, X } from 'lucide-react'
import { BrowserRouter, Link, Navigate, Route as AppRoute, Routes, useLocation } from 'react-router-dom'
const Dashboard = lazy(() => import('./pages/Dashboard').then((module) => ({ default: module.Dashboard })))
const Courses = lazy(() => import('./pages/Courses').then((module) => ({ default: module.Courses })))
const ConceptMap = lazy(() => import('./pages/ConceptMap').then((module) => ({ default: module.ConceptMap })))
const StudyRoadmap = lazy(() => import('./pages/StudyRoadmap').then((module) => ({ default: module.StudyRoadmap })))
const Resources = lazy(() => import('./pages/Resources').then((module) => ({ default: module.Resources })))
const Quizzes = lazy(() => import('./pages/Quizzes').then((module) => ({ default: module.Quizzes })))
const Progress = lazy(() => import('./pages/Progress').then((module) => ({ default: module.Progress })))
const Login = lazy(() => import('./pages/Login').then((module) => ({ default: module.Login })))
const Account = lazy(() => import('./pages/Account').then((module) => ({ default: module.Account })))
import './styles.css'

type Page = 'dashboard' | 'courses' | 'concepts' | 'roadmap' | 'resources' | 'quizzes' | 'progress' | 'account'
const navigation: { id: Page; label: string; icon: typeof Home }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Home }, { id: 'courses', label: 'My courses', icon: BookOpen }, { id: 'concepts', label: 'Concept map', icon: BrainCircuit }, { id: 'roadmap', label: 'Study roadmap', icon: Route }, { id: 'resources', label: 'Resources', icon: Library }, { id: 'quizzes', label: 'Quizzes', icon: Layers3 }, { id: 'progress', label: 'Progress', icon: BarChart3 }, { id: 'account', label: 'Account', icon: Settings },
]

function Loading() { return <main aria-live="polite">Loading…</main> }

function AppShell() {
  const location = useLocation(); const [open, setOpen] = useState(false)
  const page = (location.pathname.replace('/', '') || 'dashboard') as Page
  return <div className="app-shell"><aside className={open ? 'sidebar open' : 'sidebar'}><div className="brand"><div className="brand-mark"><Compass size={20} /></div><span>pathway<span className="brand-dot">.</span></span><button aria-label="Close navigation" className="close-menu" type="button" onClick={() => setOpen(false)}><X size={18} /></button></div><div className="workspace-label">MY WORKSPACE</div><nav aria-label="Primary navigation">{navigation.map(({ id, label, icon: Icon }) => <Link className={page === id ? 'nav-item active' : 'nav-item'} to={`/${id === 'dashboard' ? '' : id}`} onClick={() => setOpen(false)} key={id}><Icon aria-hidden="true" size={18} /><span>{label}</span>{page === id && <ChevronRight aria-hidden="true" size={15} />}</Link>)}</nav><div className="sidebar-bottom"><div className="streak"><Sparkles aria-hidden="true" size={16} /><div><strong>6 day streak</strong><small>Keep it going</small></div></div><Link className="profile" to="/account"><CircleUserRound aria-hidden="true" size={28} /><span><strong>Account</strong><small>Privacy and sign out</small></span></Link></div></aside><div className="content"><header className="topbar"><button aria-label="Open navigation" className="menu-button" type="button" onClick={() => setOpen(true)}><Menu aria-hidden="true" size={21} /></button><div className="breadcrumb"><span>Workspace</span><ChevronRight aria-hidden="true" size={14} /><strong>{navigation.find((item) => item.id === page)?.label}</strong></div><div className="top-actions"><button aria-label="View rankings" className="icon-button" type="button"><Trophy aria-hidden="true" size={18} /></button><button aria-label="Open account" className="avatar" type="button" onClick={() => window.location.assign('/account')}>AM</button></div></header><Suspense fallback={<Loading />}><Routes><AppRoute path="/" element={<Dashboard />} /><AppRoute path="/dashboard" element={<Dashboard />} /><AppRoute path="/courses" element={<Courses />} /><AppRoute path="/concepts" element={<ConceptMap />} /><AppRoute path="/roadmap" element={<StudyRoadmap />} /><AppRoute path="/resources" element={<Resources />} /><AppRoute path="/quizzes" element={<Quizzes />} /><AppRoute path="/progress" element={<Progress />} /><AppRoute path="/account" element={<Account />} /></Routes></Suspense></div></div>
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem('access_token')))
  return <BrowserRouter><Suspense fallback={<Loading />}>{authenticated ? <AppShell /> : <Routes><AppRoute path="/login" element={<Login onSuccess={() => setAuthenticated(true)} />} /><AppRoute path="*" element={<Navigate to="/login" replace />} /></Routes>}</Suspense></BrowserRouter>
}
