interface ConfusionMatrixProps {
  matrix: number[][]
  labels?: [string, string]
}

export function ConfusionMatrix({ matrix, labels = ['No germinate', 'Germinate'] }: ConfusionMatrixProps) {
  const max = Math.max(...matrix.flat())

  return (
    <div className="grid grid-cols-[auto_1fr_1fr] gap-1.5">
      <div />
      {labels.map((l) => (
        <div key={l} className="text-[10px] text-center text-[var(--color-text-faint)] uppercase tracking-wide pb-1">
          Pred: {l}
        </div>
      ))}
      {matrix.map((row, i) => (
        <div className="contents" key={i}>
          <div className="text-[10px] text-[var(--color-text-faint)] uppercase tracking-wide flex items-center pr-2 justify-end">
            Actual: {labels[i]}
          </div>
          {row.map((val, j) => {
            const intensity = max > 0 ? val / max : 0
            const isCorrect = i === j
            return (
              <div
                key={j}
                className="aspect-square rounded-xl flex items-center justify-center font-display font-bold text-lg border"
                style={{
                  background: isCorrect
                    ? `rgba(16, 185, 129, ${0.12 + intensity * 0.35})`
                    : `rgba(248, 113, 113, ${0.08 + intensity * 0.25})`,
                  borderColor: isCorrect ? 'rgba(16,185,129,0.3)' : 'rgba(248,113,113,0.25)',
                  color: isCorrect ? '#6ee7b7' : '#fca5a5',
                }}
              >
                {val}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}
