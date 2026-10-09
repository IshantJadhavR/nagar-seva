/** Original vector illustrations (no external images, so they never break offline). Colours come from the brand tokens. */

export function HeroIllustration({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 560 460" className={className} role="img" aria-label="City street with a reported problem pinned on a map">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#d3f3ee" /><stop offset="1" stopColor="#fff8ec" /></linearGradient>
        <linearGradient id="road" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2b3b4f" /><stop offset="1" stopColor="#0f1b2d" /></linearGradient>
      </defs>
      <rect width="560" height="460" rx="32" fill="url(#sky)" />
      <circle cx="450" cy="92" r="46" fill="#ffc368" opacity=".9" /><circle cx="450" cy="92" r="64" fill="#ffc368" opacity=".25" />
      {/* skyline */}
      <g fill="#a8e6dd"><rect x="30" y="190" width="70" height="170" rx="6" /><rect x="110" y="140" width="64" height="220" rx="6" /><rect x="190" y="210" width="80" height="150" rx="6" /></g>
      <g fill="#74d2c8"><rect x="290" y="160" width="76" height="200" rx="6" /><rect x="378" y="205" width="62" height="155" rx="6" /><rect x="452" y="150" width="78" height="210" rx="6" /></g>
      <g fill="#fff" opacity=".85">
        {[0, 1, 2, 3].map((r) => [0, 1].map((c) => <rect key={`a${r}${c}`} x={122 + c * 26} y={158 + r * 36} width="14" height="18" rx="3" />))}
        {[0, 1, 2].map((r) => [0, 1, 2].map((c) => <rect key={`b${r}${c}`} x={304 + c * 22} y={176 + r * 40} width="12" height="18" rx="3" />))}
        {[0, 1, 2].map((r) => [0, 1, 2].map((c) => <rect key={`c${r}${c}`} x={466 + c * 22} y={168 + r * 40} width="12" height="18" rx="3" />))}
      </g>
      {/* ground + road */}
      <rect y="360" width="560" height="100" fill="url(#road)" />
      <rect y="352" width="560" height="14" fill="#e2e8f0" />
      <g fill="#ffc368"><rect x="40" y="408" width="60" height="7" rx="3" /><rect x="150" y="408" width="60" height="7" rx="3" /><rect x="260" y="408" width="60" height="7" rx="3" /><rect x="370" y="408" width="60" height="7" rx="3" /><rect x="480" y="408" width="60" height="7" rx="3" /></g>
      {/* pothole */}
      <ellipse cx="250" cy="438" rx="38" ry="9" fill="#050b14" />
      {/* street light */}
      <g><rect x="62" y="262" width="7" height="100" rx="3" fill="#143f3f" /><rect x="62" y="258" width="40" height="7" rx="3" fill="#143f3f" /><circle cx="100" cy="274" r="9" fill="#ffc368" /></g>
      {/* big map pin */}
      <g transform="translate(250 60)">
        <ellipse cx="30" cy="268" rx="26" ry="7" fill="#0f1b2d" opacity=".25" />
        <path d="M30 0C13.4 0 0 13.4 0 30c0 24 30 62 30 62s30-38 30-62C60 13.4 46.6 0 30 0z" fill="#f98b0b" transform="translate(0 150) scale(1)" />
        <circle cx="30" cy="180" r="12" fill="#fff" />
        <rect x="28" y="242" width="4" height="26" rx="2" fill="#f98b0b" />
      </g>
      {/* phone card */}
      <g transform="translate(330 232)">
        <rect width="190" height="116" rx="18" fill="#fff" stroke="#dfe6ee" />
        <rect x="16" y="16" width="70" height="10" rx="5" fill="#0f1b2d" />
        <rect x="16" y="36" width="158" height="7" rx="3.5" fill="#cbd5e1" /><rect x="16" y="50" width="120" height="7" rx="3.5" fill="#cbd5e1" />
        <rect x="16" y="74" width="62" height="24" rx="12" fill="#ffefd0" /><text x="47" y="91" textAnchor="middle" fontSize="12" fontWeight="700" fill="#b75009">High</text>
        <rect x="88" y="74" width="86" height="24" rx="12" fill="#d3f3ee" /><text x="131" y="91" textAnchor="middle" fontSize="12" fontWeight="700" fill="#146461">Roads dept.</text>
      </g>
    </svg>
  );
}

export function AuthIllustration({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 480 420" className={className} role="img" aria-label="Neighbourhood with a map pin">
      <rect width="480" height="420" rx="28" fill="#146461" />
      <circle cx="400" cy="70" r="70" fill="#1f9c92" opacity=".5" /><circle cx="60" cy="360" r="90" fill="#144f4e" />
      <g fill="#0b3a39"><rect x="40" y="220" width="70" height="140" rx="8" /><rect x="125" y="170" width="60" height="190" rx="8" /><rect x="300" y="190" width="70" height="170" rx="8" /><rect x="385" y="240" width="60" height="120" rx="8" /></g>
      <g fill="#ffc368" opacity=".9">{[0, 1, 2].map((r) => <rect key={r} x={142} y={190 + r * 40} width="26" height="16" rx="4" />)}{[0, 1, 2].map((r) => <rect key={`x${r}`} x={318} y={210 + r * 40} width="34" height="16" rx="4" />)}</g>
      <rect y="360" width="480" height="60" fill="#082828" />
      <g transform="translate(190 60)"><path d="M50 0C22.4 0 0 22.4 0 50c0 40 50 104 50 104s50-64 50-104C100 22.4 77.6 0 50 0z" fill="#f98b0b" /><circle cx="50" cy="50" r="20" fill="#fff" /></g>
      <path d="M170 330 Q240 290 310 330" stroke="#a8e6dd" strokeWidth="4" strokeDasharray="2 10" strokeLinecap="round" fill="none" />
    </svg>
  );
}

export function EmptyIllustration({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 200 140" className={className} role="img" aria-label="Nothing here yet">
      <ellipse cx="100" cy="122" rx="70" ry="9" fill="#dfe6ee" />
      <rect x="46" y="28" width="108" height="84" rx="12" fill="#fff" stroke="#cbd5e1" strokeWidth="2" />
      <rect x="62" y="46" width="52" height="8" rx="4" fill="#a8e6dd" /><rect x="62" y="64" width="76" height="6" rx="3" fill="#e2e8f0" /><rect x="62" y="78" width="60" height="6" rx="3" fill="#e2e8f0" />
      <circle cx="146" cy="40" r="18" fill="#ffc368" /><path d="M139 40l5 5 9-10" stroke="#0f1b2d" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
