/** A twelve-toothed gear: the brand's emblem. Decorative, so hidden from assistive technology. */
export function GearIcon({ size = 28 }: { size?: number }) {
  const teeth = Array.from({ length: 12 }, (_, index) => index * 30);
  return (
    <svg width={size} height={size} viewBox="-50 -50 100 100" aria-hidden="true" focusable="false">
      <g fill="currentColor">
        {teeth.map((angle) => (
          <rect key={angle} x="-7" y="-48" width="14" height="16" rx="2" transform={`rotate(${angle})`} />
        ))}
        <circle r="36" />
      </g>
      <circle r="14" fill="var(--iron)" />
      <circle r="24" fill="none" stroke="var(--iron)" strokeWidth="3" />
    </svg>
  );
}
