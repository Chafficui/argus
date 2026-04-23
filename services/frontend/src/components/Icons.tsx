interface IconProps {
  size?: number
  className?: string
  style?: React.CSSProperties
}

function makeIcon(children: React.ReactNode, fill = 'none', strokeWidth = 1.75) {
  return function Icon({ size = 16, className = '', style = {} }: IconProps) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill={fill}
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        style={style}
      >
        {children}
      </svg>
    )
  }
}

export const IconSearch = makeIcon(
  <>
    <circle cx={11} cy={11} r={8} />
    <path d="M21 21l-4.3-4.3" />
  </>
)

export const IconSources = makeIcon(
  <>
    <rect x={3} y={4} width={18} height={16} rx={2} />
    <path d="M3 10h18" />
    <path d="M8 4v6" />
  </>
)

export const IconChat = makeIcon(
  <path d="M3 12a9 9 0 1 1 3.9 7.4L3 20.5l1.1-3.9A9 9 0 0 1 3 12z" />
)

export const IconSettings = makeIcon(
  <>
    <circle cx={12} cy={12} r={3} />
    <path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z" />
  </>
)

export const IconPlus = makeIcon(
  <>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </>
)

export const IconGlobe = makeIcon(
  <>
    <circle cx={12} cy={12} r={10} />
    <path d="M2 12h20" />
    <path d="M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20z" />
  </>
)

export const IconRss = makeIcon(
  <>
    <path d="M4 11a9 9 0 0 1 9 9" />
    <path d="M4 4a16 16 0 0 1 16 16" />
    <circle cx={5} cy={19} r={1.5} />
  </>
)

export const IconArrow = makeIcon(
  <>
    <path d="M5 12h14" />
    <path d="M13 6l6 6-6 6" />
  </>
)

export const IconExternal = makeIcon(
  <>
    <path d="M15 3h6v6" />
    <path d="M10 14L21 3" />
    <path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5" />
  </>
)

export const IconClose = makeIcon(
  <>
    <path d="M18 6L6 18" />
    <path d="M6 6l12 12" />
  </>
)

export const IconRefresh = makeIcon(
  <>
    <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
    <path d="M21 3v5h-5" />
    <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
    <path d="M3 21v-5h5" />
  </>
)

export const IconTrash = makeIcon(
  <>
    <path d="M3 6h18" />
    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
  </>
)

export const IconSparkle = makeIcon(
  <path d="M12 3l2.5 5.5L20 11l-5.5 2.5L12 19l-2.5-5.5L4 11l5.5-2.5z" />
)

export const IconCopy = makeIcon(
  <>
    <rect x={9} y={9} width={13} height={13} rx={2} />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </>
)

export const IconCheck = makeIcon(
  <path d="M4 12l5 5L20 6" />
)

export const IconClock = makeIcon(
  <>
    <circle cx={12} cy={12} r={10} />
    <path d="M12 6v6l4 2" />
  </>
)
