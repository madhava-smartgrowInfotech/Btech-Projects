import { useMemo, useState } from 'react'
import { Activity, BarChart3, Crosshair, Info, RefreshCw, Ruler, Target } from 'lucide-react'
import { Badge, Button, Card, ErrorState, PageHeader, PageSkeleton, Segmented, StatCard, Table, Tabs } from '../components/ui'
import { BarCompare, ChartLegend, GroupedBars, LineCompare } from '../components/charts'
import { ModeBadge, TickerTabs, useTicker } from '../components/app/parts'
import { api } from '../lib/api'
import { useAsync, useRefresh } from '../lib/hooks'
import { DEEP_ORDER, allModels, bestBy, modelLabel } from '../lib/market'
import { fmtInt, fmtNum, fmtPct } from '../lib/format'
import { useChartTheme } from '../lib/palette'

const SHORT = { lstm: 'LSTM', lstm_attention: '+ Attention', lstm_attention_sentiment: '+ Sentiment', hybrid_federated: 'Hybrid (Fed)' }
const TABS = [
  { id: 'compare', label: 'Accuracy comparison', icon: BarChart3 },
  { id: 'training', label: 'Training and federated rounds', icon: Activity },
]

const metricColumns = [
  { key: 'mae', label: 'MAE', numeric: true, render: (r) => fmtNum(r.mae) },
  { key: 'mse', label: 'MSE', numeric: true, render: (r) => fmtNum(r.mse) },
  { key: 'rmse', label: 'RMSE', numeric: true, render: (r) => fmtNum(r.rmse) },
  { key: 'r2', label: 'R²', numeric: true, render: (r) => fmtNum(r.r2, 3) },
  { key: 'directional_accuracy', label: 'Direction', numeric: true, render: (r) => fmtPct(r.directional_accuracy) },
]

export default function Models() {
  const list = useAsync((signal) => api.tickers({ signal }), [])
  const names = useMemo(() => list.data?.tickers.map((t) => t.ticker) || [], [list.data])
  const [ticker, setTicker, params, setParams] = useTicker(names)
  const tab = params.get('tab') === 'training' ? 'training' : 'compare'
  const setTab = (t) => setParams((p) => { const n = new URLSearchParams(p); n.set('tab', t); return n }, { replace: true })
  const [tier, setTier] = useState('lstm')
  const t = useChartTheme()

  const view = useAsync((signal) => (names.length ? api.tickerMetrics(ticker, { signal }) : null), [ticker, names.length])
  const refresh = useRefresh(view, `${ticker} metrics refreshed`)
  const m = view.data

  const models = useMemo(() => allModels(m), [m])
  const deepRows = useMemo(() => models.filter((x) => x.kind === 'deep'), [models])
  const baseRows = useMemo(() => models.filter((x) => x.kind === 'baseline'), [models])
  const bestMae = bestBy(models, 'mae')
  const bestR2 = bestBy(models, 'r2', false)
  const bestDa = bestBy(models, 'directional_accuracy', false)

  const tierChoices = DEEP_ORDER.filter((k) => m?.histories?.[k]).map((k) => ({ value: k, label: SHORT[k] }))
  const activeTier = tierChoices.some((c) => c.value === tier) ? tier : tierChoices[0]?.value
  const curve = useMemo(() => {
    const h = m?.histories?.[activeTier]
    if (!h) return []
    return h.loss.map((v, i) => ({ x: i + 1, loss: v, val_loss: h.val_loss?.[i] }))
  }, [m, activeTier])

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Model comparison"
        icon={BarChart3}
        title={`How ${ticker} models stack up`}
        lead="Test-set accuracy for the four deep-model tiers and the five classical baselines, plus how each tier trained."
        actions={
          <Button variant="secondary" icon={RefreshCw} loading={view.loading && !!m} onClick={refresh}>
            Refresh
          </Button>
        }
      />

      {list.error && <ErrorState title="Could not load the ticker list" error={list.error} onRetry={list.reload} />}
      {list.loading && !list.data && <PageSkeleton kpis={4} blocks={2} />}

      {names.length > 0 && (
        <>
          <div className="toolbar">
            <TickerTabs tickers={names} value={ticker} onChange={setTicker} />
          </div>

          {view.loading && !m && <PageSkeleton kpis={4} blocks={2} />}
          {view.error && <ErrorState title={`Could not load ${ticker} metrics`} error={view.error} onRetry={view.reload} />}

          {m && (
            <div className="stack" style={{ '--gap': '22px', opacity: view.loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={view.loading}>
              <div className="grid-kpi">
                <StatCard label="Lowest error (MAE)" display={bestMae?.label || '–'} icon={Target} tone="mint" foot={bestMae ? `MAE ${fmtNum(bestMae.mae)}` : undefined} />
                <StatCard label="Best fit (R²)" display={bestR2?.label || '–'} icon={Ruler} tone="lavender" foot={bestR2 ? `R² ${fmtNum(bestR2.r2, 3)}` : undefined} />
                <StatCard label="Best direction call" display={bestDa?.label || '–'} icon={Crosshair} tone="peach" foot={bestDa ? `${fmtPct(bestDa.directional_accuracy)} of days right` : undefined} />
                <StatCard label="Test windows" value={m.deep?.lstm?.n_test ?? baseRows[0]?.n_test} format={fmtInt} icon={BarChart3} tone="sky" foot="chronological 80/20 split" />
              </div>

              <div className="row between">
                <Tabs tabs={TABS} value={tab} onChange={setTab} name="models-tab" label="Model views" />
                <ModeBadge mode={m.mode} />
              </div>

              {tab === 'compare' && (
                <div className="stack" style={{ '--gap': '22px' }}>
                  <div className="grid-2">
                    <Card title="Deep-model ablation" subtitle="Each tier adds one idea: attention, then sentiment, then federated averaging.">
                      <div className="legend-row">
                        <ChartLegend items={[{ label: 'MAE', color: t.lavender }, { label: 'RMSE', color: t.sky }]} />
                      </div>
                      <GroupedBars
                        data={deepRows.map((r) => ({ x: SHORT[r.key], MAE: +r.mae.toFixed(2), RMSE: +r.rmse.toFixed(2) }))}
                        series={[{ key: 'MAE', name: 'MAE', color: t.lavender }, { key: 'RMSE', name: 'RMSE', color: t.sky }]}
                        valueFormat={(v) => fmtNum(v)}
                        label={`${ticker} MAE and RMSE for each deep-model tier`}
                      />
                    </Card>
                    <Card title="Every model by MAE" subtitle="Lower is better. Deep tiers in lavender, classical baselines in blue.">
                      <BarCompare
                        horizontal
                        yWidth={150}
                        height={330}
                        name="MAE"
                        valueFormat={(v) => fmtNum(v)}
                        data={[...models].sort((a, b) => a.mae - b.mae).map((r) => ({ name: r.label, value: +r.mae.toFixed(2), highlight: r.kind === 'deep' }))}
                        highlightColor={t.lavender}
                        color={t.sky}
                        label={`${ticker} MAE for all nine models`}
                      />
                    </Card>
                  </div>

                  <Card title="Deep-model tiers" subtitle="Test-set metrics. The best MAE is highlighted.">
                    <Table
                      caption={`${ticker} deep-model metrics`}
                      rows={deepRows}
                      rowKey={(r) => r.key}
                      pageSize={0}
                      highlight={(r) => r.key === bestMae?.key}
                      columns={[{ key: 'label', label: 'Model', sortable: false }, ...metricColumns]}
                    />
                  </Card>
                  <Card title="Classical baselines" subtitle="ARIMA, SARIMAX, Prophet, Random Forest and SVR on the same split.">
                    <Table
                      caption={`${ticker} baseline metrics`}
                      rows={baseRows}
                      rowKey={(r) => r.key}
                      pageSize={0}
                      highlight={(r) => r.key === bestMae?.key}
                      columns={[{ key: 'label', label: 'Model', sortable: false }, ...metricColumns]}
                    />
                  </Card>
                  {m.sentiment?.note && (
                    <div className="note warn" role="note">
                      <Info size={18} aria-hidden="true" />
                      <span>
                        <b>Sentiment tier input:</b> {m.sentiment.note}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {tab === 'training' && (
                <div className="grid-2">
                  <Card
                    title="Training and validation loss"
                    subtitle={`${modelLabel(activeTier)} over ${curve.length} epochs (scaled MSE).`}
                    actions={tierChoices.length > 0 && <Segmented name="tier" label="Tier" value={activeTier} onChange={setTier} options={tierChoices} />}
                  >
                    {curve.length === 0 ? (
                      <p className="muted">No loss curve was saved for this tier.</p>
                    ) : (
                      <>
                        <div className="legend-row">
                          <ChartLegend items={[{ label: 'Training loss', color: t.lavender }, { label: 'Validation loss', color: t.peach }]} />
                        </div>
                        <LineCompare
                          data={curve}
                          dots={false}
                          xFormat={(v) => `Epoch ${v}`}
                          valueFormat={(v) => (v == null ? '–' : Number(v).toFixed(4))}
                          series={[{ key: 'loss', name: 'Training loss', color: t.lavender }, { key: 'val_loss', name: 'Validation loss', color: t.peach, dashed: true }]}
                          label={`${ticker} ${modelLabel(activeTier)} training and validation loss per epoch`}
                        />
                      </>
                    )}
                  </Card>
                  <Card title="Federated averaging rounds" subtitle="Each ticker trains locally, then weights are averaged (FedAvg).">
                    {m.federated_rounds?.length ? (
                      <>
                        <LineCompare
                          data={m.federated_rounds.map((r) => ({ x: r.round, loss: r.mean_local_loss }))}
                          xFormat={(v) => `Round ${v}`}
                          valueFormat={(v) => Number(v).toFixed(4)}
                          series={[{ key: 'loss', name: 'Mean local loss', color: t.mint }]}
                          label="Mean local loss per federated round"
                          height={240}
                        />
                        <div className="row" style={{ marginTop: 12 }}>
                          {m.federated_rounds.map((r) => (
                            <Badge key={r.round} tone="mint">
                              Round {r.round}: {r.mean_local_loss.toFixed(4)}
                            </Badge>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="muted">No federated rounds were recorded.</p>
                    )}
                  </Card>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
