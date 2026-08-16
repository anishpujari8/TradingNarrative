import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

// Contextual glossary tooltips for industry terms inside essays.
// Applied to the Tech & AI, Trading Business & Finance, and Delivery & Systems pillars only.
export const GLOSSARY_PILLARS = ["tech-business", "finance", "delivery"];

// Each entry: key, display term, matcher regexes (checked in order), plain-English definition.
// Case-sensitive regexes are used where lowercase collisions exist (VaR vs "var", API, P&L...).
export const GLOSSARY_TERMS = [
  {
    key: "demurrage",
    term: "Demurrage",
    patterns: [/\bdemurrages?\b/i],
    definition:
      "A penalty charge paid to a shipowner when loading or unloading takes longer than the agreed time (laytime). The clock starts the moment laytime runs out.",
  },
  {
    key: "etrm",
    term: "ETRM",
    patterns: [/\bETRM\b/i],
    definition:
      "Energy Trading and Risk Management software, the system energy desks use to capture deals, track positions, and manage risk from trade to settlement.",
  },
  {
    key: "ctrm",
    term: "CTRM",
    patterns: [/\bCTRM\b/i],
    definition:
      "Commodity Trading and Risk Management software, the broader cousin of ETRM that also handles physical commodities like metals, agri, and freight.",
  },
  {
    key: "mark-to-market",
    term: "Mark-to-Market",
    patterns: [/\bmark(?:ed|ing)?[- ]to[- ]market\b/i, /\bMtM\b/],
    definition:
      "Revaluing a position at today's market price instead of the price you paid, so the books always show what it is actually worth right now.",
  },
  {
    key: "commodity-risk",
    term: "Commodity Risk",
    patterns: [/\bcommodity (?:price )?risks?\b/i],
    definition:
      "The risk that moves in commodity prices (oil, metals, grain, power) hurt your position or business before you can react.",
  },
  {
    key: "position-limit",
    term: "Position Limit",
    patterns: [/\bposition limits?\b/i],
    definition:
      "A cap on how large a trader's or firm's position may grow, set by exchanges, regulators, or internal risk teams to contain potential damage.",
  },
  {
    key: "counterparty-risk",
    term: "Counterparty Risk",
    patterns: [/\bcounterparty risks?\b/i],
    definition:
      "The risk that the other side of your trade fails to pay or deliver. You can be right on the market and still lose because they defaulted.",
  },
  {
    key: "nomination",
    term: "Nomination",
    patterns: [/\bnominations?\b/i],
    definition:
      "The formal notice naming the vessel, quantity, and dates for a physical delivery, telling the other side exactly how the cargo will move.",
  },
  {
    key: "scheduling",
    term: "Scheduling",
    patterns: [/\bscheduling\b/i],
    definition:
      "Planning the physical movement of cargoes and deliveries, which vessel, which berth, which dates, so paper contracts turn into actual flows.",
  },
  {
    key: "isda",
    term: "ISDA",
    patterns: [/\bISDA\b/],
    definition:
      "The International Swaps and Derivatives Association, best known for the ISDA Master Agreement, the standard legal contract behind most over-the-counter derivatives.",
  },
  {
    key: "crack-spread",
    term: "Crack Spread",
    patterns: [/\bcrack spreads?\b/i],
    definition:
      "The margin a refinery earns turning crude oil into products like petrol and diesel, traded as the price gap between crude and product futures.",
  },
  {
    key: "contango",
    term: "Contango",
    patterns: [/\bcontango\b/i],
    definition:
      "A market where future delivery costs more than buying today. The curve slopes upward, which often pays traders to store now and sell later.",
  },
  {
    key: "backwardation",
    term: "Backwardation",
    patterns: [/\bbackwardation\b/i],
    definition:
      "A market where buying today costs more than future delivery. The curve slopes downward, usually a sign that immediate supply is tight.",
  },
  {
    key: "api-gravity",
    term: "API (crude grade)",
    patterns: [/\bAPI gravity\b/, /\b°API\b/],
    definition:
      "A scale for how light or heavy a crude oil is. Higher API means lighter crude, which is usually easier to refine into valuable products.",
  },
  {
    key: "fpso",
    term: "FPSO",
    patterns: [/\bFPSO\b/],
    definition:
      "A Floating Production, Storage and Offloading vessel, a ship that produces oil at sea, stores it onboard, and offloads it to tankers.",
  },
  {
    key: "freight-differential",
    term: "Freight Differential",
    patterns: [/\bfreight differentials?\b/i],
    definition:
      "The price adjustment for what it costs to ship a commodity between locations, the reason the same barrel is worth different amounts in different ports.",
  },
  {
    key: "pnl",
    term: "P&L",
    patterns: [/\bP&L\b/, /\bprofit and loss\b/i],
    definition:
      "Profit and Loss, the running score of how much a trade, book, or desk has made or lost over a period.",
  },
  {
    key: "var",
    term: "VaR",
    patterns: [/\bVaR\b/, /\bvalue at risk\b/i],
    definition:
      "Value at Risk, an estimate of the most a portfolio could lose over a set period at a given confidence level. A standard yardstick for desk risk.",
  },
  {
    key: "algo-trading",
    term: "Algo Trading",
    patterns: [/\balgo(?:rithmic)? trading\b/i],
    definition:
      "Using computer programs to place and manage orders automatically based on rules, from simple execution slicing to fully automated strategies.",
  },
  {
    key: "ml-trading",
    term: "Machine Learning in Trading",
    patterns: [/\bmachine[- ]learning\b/i],
    definition:
      "Using models that learn patterns from data to drive signals, forecasts, or execution, instead of hand-coding every rule up front.",
  },
];

// Inline term with a hover (desktop) / tap (mobile) definition card.
export const GlossaryTerm = ({ entry, children }) => {
  const [open, setOpen] = useState(false);
  const timer = useRef(null);
  const show = () => { clearTimeout(timer.current); setOpen(true); };
  const hideSoon = () => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setOpen(false), 140);
  };
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <span
          className="glossary-term"
          onMouseEnter={show}
          onMouseLeave={hideSoon}
          onClick={(e) => { e.preventDefault(); show(); }}
          role="button"
          tabIndex={0}
          aria-label={`Definition of ${entry.term}`}
          data-testid={`glossary-term-${entry.key}`}
        >
          {children}
        </span>
      </PopoverTrigger>
      <PopoverContent
        side="top"
        sideOffset={8}
        onMouseEnter={show}
        onMouseLeave={hideSoon}
        onOpenAutoFocus={(e) => e.preventDefault()}
        className="w-72 rounded-xl border-accent/30 bg-popover/95 backdrop-blur-md shadow-lg p-4"
        data-testid={`glossary-tooltip-${entry.key}`}
      >
        <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-accent">{entry.term}</span>
        <p className="text-sm text-foreground/90 leading-relaxed mt-1.5">{entry.definition}</p>
        <Link
          to="/glossary"
          className="inline-block text-xs text-muted-foreground hover:text-accent mt-2.5 transition-colors duration-150"
          data-testid={`glossary-tooltip-link-${entry.key}`}
        >
          Full glossary →
        </Link>
      </PopoverContent>
    </Popover>
  );
};

// Wrap the FIRST occurrence of each term across an essay, working over an array of
// strings and React elements (existing highlight <mark>s pass through untouched).
// `seen` is a per-essay Set so a term only ever gets one tooltip per read.
// `skipDropCap` avoids wrapping a match at the very start of the opening paragraph,
// where the CSS drop cap would visually split the underlined term.
export const wrapGlossaryTerms = (nodes, seen, { skipDropCap = false } = {}) => {
  let parts = Array.isArray(nodes) ? [...nodes] : [nodes];
  for (const entry of GLOSSARY_TERMS) {
    if (seen.has(entry.key)) continue;
    let matched = false;
    parts = parts.flatMap((seg, idx) => {
      if (matched || typeof seg !== "string") return [seg];
      for (const re of entry.patterns) {
        let m = seg.match(re);
        let offset = 0;
        if (m && skipDropCap && idx === 0 && m.index === 0) {
          // re-search past the drop-cap letter
          const rest = seg.slice(1);
          m = rest.match(re);
          offset = 1;
        }
        if (m) {
          matched = true;
          seen.add(entry.key);
          const start = m.index + offset;
          const end = start + m[0].length;
          return [
            seg.slice(0, start),
            <GlossaryTerm key={`g-${entry.key}-${idx}`} entry={entry}>{m[0]}</GlossaryTerm>,
            seg.slice(end),
          ];
        }
      }
      return [seg];
    });
  }
  return parts;
};
