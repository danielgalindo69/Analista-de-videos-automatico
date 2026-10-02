const paths = {
  activity: <><path d="M3 12h4l2.5-7 5 14 2.5-7h4" /></>,
  brain: <><path d="M9.5 4.5A3 3 0 0 0 5 7a3 3 0 0 0 .5 5.5A3.5 3.5 0 0 0 9 18h1V6a2 2 0 0 0-.5-1.5Z" /><path d="M14.5 4.5A3 3 0 0 1 19 7a3 3 0 0 1-.5 5.5A3.5 3.5 0 0 1 15 18h-1V6a2 2 0 0 1 .5-1.5Z" /><path d="M6 9h4M14 9h4M7 14h3M14 14h3" /></>,
  close: <><path d="m7 7 10 10" /><path d="m17 7-10 10" /></>,
  external: <><path d="M14 5h5v5" /><path d="M10 14 19 5" /><path d="M19 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" /></>,
  film: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M7 5v14M17 5v14M3 9h4M17 9h4M3 15h4M17 15h4" /></>,
  lock: <><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  play: <path d="m9 7 8 5-8 5V7Z" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="m16 16 4 4" /></>,
  server: <><rect x="4" y="4" width="16" height="6" rx="2" /><rect x="4" y="14" width="16" height="6" rx="2" /><path d="M8 7h.01M8 17h.01" /></>,
  spark: <><path d="m12 3 1.3 4.2L17 9l-3.7 1.8L12 15l-1.3-4.2L7 9l3.7-1.8L12 3Z" /><path d="m18 15 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7L18 15Z" /></>,
  trend: <><path d="M4 17 10 11l4 4 6-8" /><path d="M15 7h5v5" /></>,
  youtube: <><path d="M21 12c0 3-.4 5-1 5.7-.8.8-4.2 1.1-8 1.1s-7.2-.3-8-1.1C3.4 17 3 15 3 12s.4-5 1-5.7c.8-.8 4.2-1.1 8-1.1s7.2.3 8 1.1c.6.7 1 2.7 1 5.7Z" /><path d="m10 9 5 3-5 3V9Z" /></>,
}

export function Icon({ name, size = 20, strokeWidth = 1.8, className = '', ...props }) {
  return (
    <svg aria-hidden="true" className={`icon ${className}`} fill="none" height={size} viewBox="0 0 24 24" width={size} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={strokeWidth} {...props}>
      {paths[name]}
    </svg>
  )
}
