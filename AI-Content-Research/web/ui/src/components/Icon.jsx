import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faYoutube } from '@fortawesome/free-brands-svg-icons'
import {
  faArrowUpRightFromSquare,
  faBrain,
  faCheck,
  faChartLine,
  faCloud,
  faEye,
  faEyeSlash,
  faFilm,
  faGear,
  faKey,
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
  check: faCheck,
  close: faXmark,
  cloud: faCloud,
  eye: faEye,
  eyeOff: faEyeSlash,
  external: faArrowUpRightFromSquare,
  film: faFilm,
  gear: faGear,
  key: faKey,
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
