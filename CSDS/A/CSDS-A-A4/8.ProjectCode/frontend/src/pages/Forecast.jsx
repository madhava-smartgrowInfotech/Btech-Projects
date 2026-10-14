import { useState } from 'react'
import { BarChart2, Brain, Gauge, LineChart as LineIcon, Package, RefreshCw, Sigma, Table2, Target, TrendingUp } from 'lucide-react'
import { BarCompare, ChartLegend, LineCompare } from '../components/charts'
import { Stagger } from '../components/motion'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  KeyValueList,
  Modal,
  PageHeader,
  PageSkeleton,
  StatCard,
  Table,
  Tabs,
  useToast,
} from '../components/ui'
import { api } from '../lib/api'
import { celebrate } from '../lib/confetti'
import { fmtCompact, fmtInt, fmtNum, monthLabel, timeAgo } from '../lib/format'
import { useChartTheme } from '../lib/palette'
import { useApi } from '../lib/useApi'

const FORECASTERS = [
  ['random_forest', 'Random Forest (proposed)'],
  ['baseline_last_value', "Last month's value"],
  ['baseline_moving_avg_3', '3-month moving average'],
]

export default function Forecast() {
  const toast = useToast()
  const t = useChartTheme()
  const [confirm, setConfirm] = useState(false)
  const [training, setTraining] = useState(false)
  const [view, setView] = useState('chart')
  const { data, error, loading, reload } = useApi(async (o) => {
    const [fm, fc] = await Promise.all([api.forecastMetrics(o), api.forecast(o).catch(() => null)])
    return { fm, fc }
  })

  const train = async () => {
    setConfirm(false)
    setTraining(true)
    try {
      const r = await api.train()
      toast({ kind: 'success', title: 'Forecaster retrained', message: `MAPE ${r.random_forest.mape}% · R² ${r.random_forest.r2} · ${r.train_seconds}s` })
      celebrate('train')
      await reload({ quiet: true })
    } catch (e) {
      toast({ kind: 'error', title: 'Training failed', message: e.message })
    } finally {
      setTraining(false)
    }
  }

  const header = (
    <PageHeader
      eyebrow="Objective 2 · Demand prediction"
      icon={TrendingUp}
      title="Random Forest demand forecast"
      lead="Each region's next-month orders are predicted from lags, rolling averages, seasonality (festival months), promotions and region attributes. The last months are held out for evaluation; two naive forecasters show what the model adds."
      actions={
        <Button icon={RefreshCw} variant="secondary" loading={training} onClick={() => setConfirm(true)}>
          {training ? 'Training…' : data?.fm?.random_forest ? 'Retrain' : 'Train forecaster'}
        </Button>
      }
    />
  )

  const modal = (
    <Modal
      open={confirm}
      onClose={() => setConfirm(false)}
      title="Retrain the forecaster?"
      description="Fits a 400-tree Random Forest on all but the last 6 months and overwrites models/rf_demand.joblib. It takes around 10 seconds."
      footer={
        <>
          <Button variant="ghost" onClick={() => setConfirm(false)}>
            Cancel
          </Button>
          <Button icon={Brain} onClick={train} data-autofocus>
            Train now
          </Button>
        </>
      }
    />
  )

  if (loading)
    return (
      <>
        {header}
        <PageSkeleton />
      </>
    )
  if (error)
    return (
      <>
        {header}
        <ErrorState title="Could not load the forecast" error={error} onRetry={reload} />
      </>
    )

  const { fm, fc } = data
  if (!fm?.random_forest)
    return (
      <>
        {header}
        {modal}
        <EmptyState
          icon={Brain}
          title="The forecaster is not trained yet"
          message="Train the Random Forest on the historical orders to unlock demand forecasts and hub planning."
          action={
            <Button icon={Brain} loading={training} onClick={train}>
              Train forecaster
            </Button>
          }
        />
      </>
    )

  const rf = fm.random_forest
  const base = fm.baseline_last_value
  const imp = fm.feature_importance.slice(0, 10)
  const detail = fm.last_period_detail
  const fcRows = fc ? [...fc.regions].sort((a, b) => b.forecast - a.forecast) : []
  const fcMax = fcRows[0]?.forecast || 1

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      {header}
      {modal}

      <Stagger className="grid-kpi">
        <Stagger.Item>
          <StatCard
            label="MAPE (held-out)"
            value={rf.mape}
            format={(v) => `${v.toFixed(2)}%`}
            icon={Target}
            tone="lavender"
            delta={{ value: rf.mape - base.mape, text: `${(base.mape - rf.mape).toFixed(1)} pts`, good: 'down', label: 'better than last-value' }}
          />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Mean absolute error" value={rf.mae} format={fmtInt} icon={Sigma} tone="mint" foot={`orders · baseline ${fmtInt(base.mae)}`} />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="R² score" value={rf.r2} format={(v) => v.toFixed(3)} icon={Gauge} tone="sky" foot={`baseline ${base.r2}`} />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard
            label={fc ? `Forecast for ${monthLabel(fc.period)}` : 'Next-month forecast'}
            value={fc?.total}
            display={fc ? undefined : '–'}
            format={fmtCompact}
            icon={Package}
            tone="peach"
            foot="orders across the network"
          />
        </Stagger.Item>
      </Stagger>

      <div className="grid-2 wide-left">
        <Card title="Forecaster comparison" subtitle={`Tested on ${fm.test_periods} (${fmtInt(fm.test_rows)} rows)`} hover={false}>
          <Table
            caption="Forecast accuracy of the Random Forest and two naive baselines"
            rows={FORECASTERS.map(([k, label]) => ({ k, label, ...fm[k] }))}
            rowKey={(r) => r.k}
            pageSize={0}
            highlight={(r) => r.k === 'random_forest'}
            columns={[
              { key: 'label', label: 'Forecaster', sortable: false },
              { key: 'mae', label: 'MAE', numeric: true, render: (r) => fmtInt(r.mae) },
              { key: 'rmse', label: 'RMSE', numeric: true, render: (r) => fmtInt(r.rmse) },
              { key: 'mape', label: 'MAPE', numeric: true, render: (r) => `${r.mape}%` },
              { key: 'r2', label: 'R²', numeric: true },
            ]}
          />
        </Card>
        <Card title="Training run" subtitle={`Last trained ${timeAgo(fm.trained_at)}`}>
          <KeyValueList
            items={[
              ['Trained at', `${fm.trained_at.slice(0, 16).replace('T', ' ')} UTC`],
              ['Training months', fm.train_periods],
              ['Training rows', fmtInt(fm.train_rows)],
              ['Test months', fm.test_periods],
              ['Test rows', fmtInt(fm.test_rows)],
              ['Fit time', `${fm.train_seconds} s`],
            ]}
          />
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Feature importance" subtitle="Top 10 drivers of the Random Forest">
          <BarCompare
            horizontal
            height={380}
            yWidth={130}
            name="Importance"
            data={imp.map((f, i) => ({ name: f.feature, value: f.importance, highlight: i === 0 }))}
            valueFormat={(v) => fmtNum(v, 3)}
            label="Bar chart of feature importance"
          />
        </Card>
        <Card title={fc ? `Forecast for ${monthLabel(fc.period, true)}` : 'Next-month forecast'} subtitle={fc ? `Network total ${fmtInt(fc.total)} orders - the demand input to the hub model` : undefined} hover={false}>
          {fc ? (
            <Table
              caption="Next-month forecast per region"
              rows={fcRows}
              rowKey={(r) => r.region_id}
              pageSize={8}
              searchKeys={['city', 'region_id']}
              searchPlaceholder="Search regions"
              initialSort={{ key: 'forecast', dir: 'desc' }}
              columns={[
                { key: 'city', label: 'Region' },
                { key: 'forecast', label: 'Forecast', numeric: true, render: (r) => fmtInt(r.forecast) },
                {
                  key: 'share',
                  label: 'Relative size',
                  sortValue: (r) => r.forecast,
                  render: (r) => (
                    <span style={{ display: 'block', width: 110, height: 8, borderRadius: 99, background: 'var(--surface-3)' }}>
                      <span style={{ display: 'block', height: '100%', width: `${(r.forecast / fcMax) * 100}%`, borderRadius: 99, background: 'var(--mint)' }} />
                    </span>
                  ),
                },
              ]}
            />
          ) : (
            <ErrorState compact title="Next-month forecast unavailable" error="The API could not produce a forecast." onRetry={reload} />
          )}
        </Card>
      </div>

      <Card
        title={`Back-test: ${monthLabel(fm.last_period, true)} actual vs predicted`}
        subtitle="The model only saw data before this month"
        hover={false}
        actions={
          <Tabs
            name="backtest"
            value={view}
            onChange={setView}
            label="Back-test view"
            tabs={[
              { id: 'chart', label: 'Chart', icon: LineIcon },
              { id: 'table', label: 'Per region', icon: Table2 },
            ]}
          />
        }
      >
        {view === 'chart' ? (
          <>
            <ChartLegend
              items={[
                { label: 'Actual', color: t.sky },
                { label: 'Predicted', color: t.peach },
              ]}
            />
            <LineCompare
              height={340}
              dots={false}
              data={detail.map((r) => ({ x: r.city, actual: r.actual, predicted: r.predicted }))}
              series={[
                { key: 'actual', name: 'Actual', color: t.sky },
                { key: 'predicted', name: 'Predicted', color: t.peach, dashed: true },
              ]}
              valueFormat={fmtInt}
              yFormat={fmtCompact}
              label="Line chart of actual versus predicted orders per region"
            />
          </>
        ) : (
          <Table
            caption="Back-test per region"
            rows={detail}
            rowKey={(r) => r.region_id}
            pageSize={10}
            searchKeys={['city', 'region_id']}
            searchPlaceholder="Search regions"
            initialSort={{ key: 'error_pct', dir: 'desc' }}
            columns={[
              { key: 'city', label: 'Region' },
              { key: 'actual', label: 'Actual', numeric: true, render: (r) => fmtInt(r.actual) },
              { key: 'predicted', label: 'Predicted', numeric: true, render: (r) => fmtInt(r.predicted) },
              {
                key: 'error_pct',
                label: 'Error',
                numeric: true,
                render: (r) => <Badge tone={r.error_pct > 15 ? 'rose' : r.error_pct > 7 ? 'peach' : 'mint'}>{r.error_pct}%</Badge>,
              },
            ]}
          />
        )}
        <p className="small muted" style={{ marginTop: 12 }}>
          <BarChart2 size={14} aria-hidden="true" style={{ verticalAlign: -2, marginRight: 6 }} />
          Mean error across {detail.length} regions: {fmtNum(detail.reduce((s, r) => s + r.error_pct, 0) / detail.length, 1)}%
        </p>
      </Card>
    </div>
  )
}
