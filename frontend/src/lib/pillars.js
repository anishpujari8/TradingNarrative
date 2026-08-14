// Shared pillar identity: accent colours + signature motifs (v3), mirroring the
// backend OG share cards (services/og_service.py) and quote cards so the pillar
// language is consistent across the entire product.
//
// Motifs: Tech & AI -> circuit traces | Business & Finance -> market sparkline
//         Personal Growth -> sunrise arcs | Delivery & Systems -> shipping route

export const PILLAR_ACCENTS = {
  "tech-business": "#7a73e8", // violet
  finance: "#1c8570", // brand teal
  lifestyle: "#c4872e", // warm amber
  delivery: "#3f7cc4", // steel blue
};

export const PILLAR_TAGLINES = {
  "tech-business": "ETRM, CTRM, and the AI wave hitting the trading desk.",
  finance: "Market mechanics, from yield curves to treatment charges.",
  lifestyle: "Life systems for operators, instrumented like trading systems.",
  delivery: "How complex platforms actually get shipped and adopted.",
};

export const pillarAccent = (slug) => PILLAR_ACCENTS[slug] || "#1c8570";

// Mascot emblem images generated per pillar (frontend/public/pillars/*.webp):
// violet circuit owl / teal sparkline bull / amber phoenix / steel-blue albatross
export const pillarMascot = (slug) =>
  PILLAR_ACCENTS[slug] ? `/pillars/${slug}.webp` : null;

export const PILLAR_MASCOT_ALTS = {
  "tech-business": "Tech & AI pillar mascot: an owl with circuit-trace wings",
  finance: "Trading, Business & Finance pillar mascot: a bull with a rising market line",
  lifestyle: "Personal Growth pillar mascot: a phoenix inside sunrise rings",
  delivery: "Delivery & Systems pillar mascot: an albatross over a waypoint route",
};

// hex -> rgba() so components can tint borders/backgrounds at any opacity
export const withAlpha = (hex, a) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
};

// Signature illustration per pillar, stroked in currentColor so the parent sets
// the accent. Designed to be woven into header backgrounds at low opacity.
export const PillarMotif = ({ category, className = "", strokeWidth = 2 }) => {
  const common = {
    viewBox: "0 0 600 300",
    fill: "none",
    stroke: "currentColor",
    strokeWidth,
    className,
    "aria-hidden": true,
    preserveAspectRatio: "xMaxYMid slice",
  };
  if (category === "finance") {
    return (
      <svg {...common}>
        <polyline points="10,250 90,215 170,232 250,175 330,196 410,140 490,158 570,95" />
        {[[10, 250], [90, 215], [170, 232], [250, 175], [330, 196], [410, 140], [490, 158], [570, 95]].map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r="4" fill="currentColor" stroke="none" />
        ))}
        <line x1="10" y1="278" x2="570" y2="278" strokeDasharray="2 8" opacity="0.6" />
      </svg>
    );
  }
  if (category === "tech-business") {
    return (
      <svg {...common}>
        <polyline points="330,40 470,40 500,70 500,150" />
        <polyline points="560,110 560,205 530,235 420,235" />
        <polyline points="360,140 440,140 465,165 465,205" />
        {[[330, 40], [500, 150], [560, 110], [420, 235], [360, 140], [465, 205]].map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="6" />
            <circle cx={x} cy={y} r="2" fill="currentColor" stroke="none" />
          </g>
        ))}
        <rect x="494" y="64" width="7" height="7" fill="currentColor" stroke="none" />
        <rect x="526" y="231" width="7" height="7" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  if (category === "lifestyle") {
    return (
      <svg {...common}>
        {[70, 130, 190, 250, 310].map((r, i) => (
          <path key={i} d={`M ${600 - r} 0 A ${r} ${r} 0 0 0 600 ${r}`} opacity={1 - i * 0.16} />
        ))}
        {[[470, 130], [520, 190], [420, 80]].map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r="3.5" fill="currentColor" stroke="none" />
        ))}
      </svg>
    );
  }
  if (category === "delivery") {
    return (
      <svg {...common}>
        <path d="M 20 260 Q 300 320 570 45" strokeDasharray="12 10" />
        {[[20, 260], [216, 252], [420, 168]].map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="7" />
            <circle cx={x} cy={y} r="2" fill="currentColor" stroke="none" />
          </g>
        ))}
        <circle cx="570" cy="45" r="12" />
        <circle cx="570" cy="45" r="4" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  return null;
};
