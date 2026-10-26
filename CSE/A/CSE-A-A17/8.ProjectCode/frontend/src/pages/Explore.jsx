import { Card, ErrorState, PageHeader, Skeleton, StatCard } from '../components/ui'
import { BarBlocks, ChartCard, Gate, HBarBlocks, LineBlocks } from '../components/app/common'
import { PALETTE } from '../components/ui/palette'
import { useApi } from '../lib/useApi'
import { usePipeline } from '../lib/pipeline'
import { fmtInt } from '../lib/format'

export default function Explore() {
  const { state } = usePipeline()
  const ready = Boolean(state?.data_loaded)
  const { data, error, loading, reload } = useApi('/api/explore', { enabled: ready })

  return (
    <>
      <PageHeader
        eyebrow="02 · Data exploration"
        title="Explore demand"
        description="Sales trends, top products and the category, channel and price mix. Demand means units sold."
      />
      <Gate ok={ready} loading={!state} title="Upload your data first" to="/app/upload" cta="Go to Data upload">
        {error ? (
          <ErrorState title="Could not build the exploration charts" error={error} onRetry={reload} />
        ) : loading || !data ? (
          <div className="page-stack">
            <div className="metric-grid">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} height={120} />
              ))}
            </div>
            <Skeleton height={320} />
            <Skeleton height={320} />
          </div>
        ) : (
          <div className="page-stack">
            <div className="metric-grid">
              <StatCard label="Units sold" value={data.total_units} />
              <StatCard label="Product-days" value={data.rows} hint="Rows in the daily demand table" />
              <StatCard label="Days covered" value={data.daily.length} />
            </div>

            <ChartCard
              title="Daily total demand"
              height={300}
              summary={`Daily total units sold across ${fmtInt(data.daily.length)} days.`}
            >
              <LineBlocks data={data.daily} xKey="date" series={[{ key: 'demand', name: 'Units sold', color: PALETTE.coral }]} />
            </ChartCard>

            <div className="two-col">
              <ChartCard title="Monthly total demand" summary="Total units sold per month.">
                <BarBlocks data={data.monthly} xKey="month" yKey="demand" name="Units sold" color={PALETTE.lime} />
              </ChartCard>
              <ChartCard title="Weekly total demand" summary="Total units sold per week.">
                <LineBlocks data={data.weekly} xKey="week" series={[{ key: 'demand', name: 'Units sold', color: PALETTE.sky }]} dots />
              </ChartCard>
            </div>

            <ChartCard title="Top 10 products by total demand" summary="The ten article ids with the most units sold.">
              <HBarBlocks data={data.top_products} labelKey="article_id" valueKey="demand" name="Units sold" labelWidth={110} />
            </ChartCard>

            <div className="two-col">
              {data.department && (
                <ChartCard title="Demand by department" summary="Units sold per department, top 15.">
                  <BarBlocks data={data.department} xKey="label" yKey="demand" name="Units sold" color={PALETTE.amber} />
                </ChartCard>
              )}
              {data.colour && (
                <ChartCard title="Demand by colour" summary="Units sold per colour group, top 15.">
                  <BarBlocks data={data.colour} xKey="label" yKey="demand" name="Units sold" color={PALETTE.sky} />
                </ChartCard>
              )}
              {data.channel && (
                <ChartCard title="Demand by sales channel" summary="Units sold per sales channel id.">
                  <BarBlocks data={data.channel} xKey="label" yKey="demand" name="Units sold" color={PALETTE.coral} />
                </ChartCard>
              )}
              <ChartCard title="Price distribution" summary="Histogram of the average daily price per product, 50 bins.">
                <BarBlocks data={data.price_hist} xKey="label" yKey="count" name="Product-days" color={PALETTE.lime} />
              </ChartCard>
            </div>
            {!data.channel && <Card flat>No sales_channel_id column in the data, so the channel chart is skipped.</Card>}
          </div>
        )}
      </Gate>
    </>
  )
}
