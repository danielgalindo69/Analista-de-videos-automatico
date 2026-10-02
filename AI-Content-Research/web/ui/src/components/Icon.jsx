import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faYoutube } from '@fortawesome/free-brands-svg-icons'
import {
  faArrowUpRightFromSquare,
  faBrain,
  faChartLine,
  faFilm,
  faLock,
  faMagnifyingGlass,
  faPlay,
  faServer,
  faWandMagicSparkles,
  faWaveSquare,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

const icons = {
  activity: faWaveSquare,
  brain: faBrain,
  close: faXmark,
  external: faArrowUpRightFromSquare,
  film: faFilm,
  lock: faLock,
  play: faPlay,
  search: faMagnifyingGlass,
  server: faServer,
  spark: faWandMagicSparkles,
  trend: faChartLine,
  youtube: faYoutube,
}

export function Icon({ name, size = 20, className = '', ...props }) {
  const icon = icons[name]
  if (!icon) return null

  return (
    <FontAwesomeIcon
      aria-hidden="true"
      className={`icon ${className}`}
      icon={icon}
      style={{ fontSize: size }}
      {...props}
    />
  )
}
