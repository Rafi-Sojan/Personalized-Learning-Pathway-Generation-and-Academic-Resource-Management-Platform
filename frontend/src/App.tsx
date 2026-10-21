import { useState } from 'react'
import { BarChart3, BookOpen, BrainCircuit, ChevronRight, CircleUserRound, Compass, Home, Layers3, Library, Menu, Route, Sparkles, Trophy, X } from 'lucide-react'
import { Dashboard } from './pages/Dashboard'
import { Courses } from './pages/Courses'
import { ConceptMap } from './pages/ConceptMap'
import { StudyRoadmap } from './pages/StudyRoadmap'
import { Resources } from './pages/Resources'
import { Quizzes } from './pages/Quizzes'
import { Progress } from './pages/Progress'
import './styles.css'

type Page = 'dashboard' | 'courses' | 'concepts' | 'roadmap' | 'resources' | 'quizzes' | 'progress'

const navigation: { id: Page; label: string; icon: typeof Home }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Home }, { id: 'courses', label: 'My courses', icon: BookOpen }, { id: 'concepts', label: 'Concept map', icon: BrainCircuit }, { id: 'roadmap', label: 'Study roadmap', icon: Route }, { id: 'resources', label: 'Resources', icon: Library }, { id: 'quizzes', label: 'Quizzes', icon: Layers3 }, { id: 'progress', label: 'Progress', icon: BarChart3 },
]

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [open, setOpen] = useState(false)
  const CurrentPage = { dashboard: Dashboard, courses: Courses, concepts: ConceptMap, roadmap: StudyRoadmap, resources: Resources, quizzes: Quizzes, progress: Progress }[page]
  return <div className="app-shell"><aside className={open ? 'sidebar open' : 'sidebar'}><div className="brand"><div className="brand-mark"><Compass size={20} /></div><span>pathway<span className="brand-dot">.</span></span><button className="close-menu" onClick={() => setOpen(false)}><X size={18} /></button></div><div className="workspace-label">MY WORKSPACE</div><nav>{navigation.map(({ id, label, icon: Icon }) => <button className={page === id ? 'nav-item active' : 'nav-item'} onClick={() => { setPage(id); setOpen(false) }} key={id}><Icon size={18} /><span>{label}</span>{page === id && <ChevronRight size={15} />}</button>)}</nav><div className="sidebar-bottom"><div className="streak"><Sparkles size={16} /><div><strong>6 day streak</strong><small>Keep it going</small></div></div><button className="profile"><CircleUserRound size={28} /><span><strong>Alex Morgan</strong><small>Student account</small></span></button></div></aside><div className="content"><header className="topbar"><button className="menu-button" onClick={() => setOpen(true)}><Menu size={21} /></button><div className="breadcrumb"><span>Workspace</span><ChevronRight size={14} /><strong>{navigation.find((item) => item.id === page)?.label}</strong></div><div className="top-actions"><button className="icon-button"><Trophy size={18} /></button><button className="avatar">AM</button></div></header><CurrentPage /></div></div>
}
