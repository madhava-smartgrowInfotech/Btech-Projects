/** Colour for the i-th paper of a hall (fixed categorical order; codes are always printed as well). */
export function paperColor(index: number) {
  return index < 8 ? `var(--paper-${index + 1})` : "var(--paper-other)";
}

/** Readable text on a paper colour. */
export function paperInk(index: number) {
  // Light-mode yellow, aqua and pink need dark ink; the rest take white.
  return [3, 4].includes(index) ? "#1a1a19" : "#ffffff";
}
