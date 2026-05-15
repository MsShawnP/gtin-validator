import { useEffect, useRef } from 'react'
import styles from './NavigationSidebar.module.css'

interface Section {
  id: string
  label: string
}

const GROUPS: { title: string; sections: Section[] }[] = [
  {
    title: 'Validation Results',
    sections: [
      { id: 'issues', label: 'Issues by Severity' },
      { id: 'detail', label: 'Full Item Detail' },
      { id: 'corrections', label: 'Check Digit Corrections' },
      { id: 'hierarchy', label: 'Packaging Hierarchy' },
    ],
  },
  {
    title: 'Deep Analysis',
    sections: [
      { id: 'summary', label: 'Executive Summary' },
      { id: 'roadmap', label: 'Prioritized Fix Plan' },
      { id: 'retailer', label: 'Retailer Readiness' },
      { id: 'cost', label: 'Cost of Inaction' },
      { id: 'gtin14', label: 'Case GTIN Generator' },
    ],
  },
]

interface Props {
  activeSection: string
  onSectionChange: (id: string) => void
  children: React.ReactNode
}

export default function NavigationSidebar({
  activeSection,
  onSectionChange,
  children,
}: Props) {
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ids = GROUPS.flatMap((g) => g.sections.map((s) => s.id))
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter(Boolean) as HTMLElement[]

    if (!elements.length) return

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            onSectionChange(entry.target.id)
            break
          }
        }
      },
      { rootMargin: '-20% 0px -70% 0px' },
    )

    elements.forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [onSectionChange])

  function scrollTo(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className={styles.layout}>
      <nav className={styles.sidebar}>
        {GROUPS.map((group) => (
          <div key={group.title} className={styles.group}>
            <div className={styles.groupTitle}>{group.title}</div>
            {group.sections.map((s) => (
              <button
                key={s.id}
                className={`${styles.link} ${activeSection === s.id ? styles.linkActive : ''}`}
                onClick={() => scrollTo(s.id)}
              >
                {s.label}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <div className={styles.content} ref={contentRef}>
        {children}
      </div>
    </div>
  )
}
