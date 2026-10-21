import { useCallback } from 'react'
import { useAsync } from '../hooks/useAsync'
import { getCourses } from '../services/courses'

export function Courses() {
  const { data, loading } = useAsync(useCallback(() => getCourses(), []), [])
  return <main><div className="eyebrow">Learning library</div><h1>My courses</h1><p className="lede">A clear view of everything you are building.</p><div className="course-grid">{loading ? <p>Loading courses…</p> : data.map((course) => <article className="course-card" key={course.id}><span className="course-code">{course.code}</span><h2>{course.title}</h2><p>{course.description}</p><div className="progress"><i style={{ width: `${course.progress}%` }} /></div><small>{course.progress}% complete · {course.concept_count} concepts</small></article>)}</div></main>
}
