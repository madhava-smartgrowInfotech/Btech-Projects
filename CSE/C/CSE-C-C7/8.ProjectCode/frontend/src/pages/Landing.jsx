import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, BarChart3, Compass, Eye, ListChecks, Target, TrendingUp } from 'lucide-react'
import { Button, Card, Container } from '../components/ui'
import { CountUp, InkRule, MagneticButton, MaskHeadline, Marquee, Reveal, SlideUp, Stagger } from '../components/motion'
import { useAuth } from '../lib/auth'
import { get } from '../lib/api'
import { useApi } from '../lib/useApi'
import { ACTION_COUNT } from '../lib/format'

const STEPS = [
  ['Create your profile', 'Education, skill level, interests, topics and goals. Comma-separated values work best.'],
  ['Get ranked courses', 'Every course is scored on content match, skill fit, topic fit, behavior and predicted success.'],
  ['Learn and interact', 'Quizzes, content reviews, discussions and completions are logged as you go.'],
  ['Watch it adapt', 'The next ranking reflects what you actually did, with the reasons spelled out.'],
]

const FEATURES = [
  { icon: Target, title: 'Profile-aware matching', body: 'Education, skill level, topics and goals shape every recommendation.' },
  { icon: TrendingUp, title: 'Learns from behavior', body: 'Views, quizzes, discussions and completions refine future suggestions.' },
  { icon: ListChecks, title: 'Clear next actions', body: 'Review content, take a quiz, join a discussion or continue your path.' },
  { icon: Eye, title: 'Transparent models', body: 'Metrics, confusion matrices and a fairness audit come from the local training run.', to: '/analytics' },
]

function useCatalogStats() {
  const q = useApi(() => get('/api/courses'), [])
  const stats = useMemo(() => {
    const courses = q.data?.courses
    if (!courses?.length) return null
    const categories = {}
    courses.forEach((c) => {
      categories[c.category] = (categories[c.category] || 0) + 1
    })
    return {
      count: courses.length,
      categories,
      categoryCount: Object.keys(categories).length,
      hours: courses.reduce((s, c) => s + (Number(c.duration_hours) || 0), 0),
      rating: courses.reduce((s, c) => s + (Number(c.rating) || 0), 0) / courses.length,
    }
  }, [q.data])
  return { stats, loading: q.loading, error: q.error }
}

export default function Landing() {
  const { user } = useAuth()
  const { stats } = useCatalogStats()
  const cta = user ? { to: '/app', label: 'Open my dashboard' } : { to: '/register', label: 'Create free account' }

  return (
    <>
      <Container>
        <section className="hero">
          <div className="hero-grid">
            <div>
              <span className="eyebrow">Personalized e-learning recommendations</span>
              <MaskHeadline className="hero-title" lines={['Your path,', 'picked with', 'reasons.']} />
              <p className="lead">
                Tell LearnPathIQ about your background, interests and goals. It ranks courses for you and names the most useful next action, and
                every suggestion arrives with its explanation, not a black-box score.
              </p>
              <div className="hero-actions">
                <MagneticButton>
                  <Button variant="primary" size="lg" to={cta.to} iconRight={ArrowRight}>
                    {cta.label}
                  </Button>
                </MagneticButton>
                <Button size="lg" to="/courses" icon={Compass}>
                  Browse courses
                </Button>
              </div>
            </div>
            <div className="checks-stack" aria-label="Catalog at a glance">
              <div>
                <div className="k">Courses</div>
                <div className="v">{stats ? stats.count : '—'}</div>
              </div>
              <div>
                <div className="k">Categories</div>
                <div className="v">{stats ? stats.categoryCount : '—'}</div>
              </div>
              <div>
                <div className="k">Avg rating</div>
                <div className="v">{stats ? stats.rating.toFixed(2) : '—'}</div>
              </div>
              <div>
                <div className="k">Action types</div>
                <div className="v">{ACTION_COUNT}</div>
              </div>
            </div>
          </div>
        </section>
      </Container>

      {stats && (
        <Marquee
          variant="lime"
          label="Catalog statistics"
          items={[
            { label: 'Courses', value: stats.count },
            { label: 'Categories', value: stats.categoryCount },
            { label: 'Learning hours', value: stats.hours },
            { label: 'Avg rating', value: stats.rating.toFixed(2) },
            { label: 'Personalized actions', value: ACTION_COUNT },
          ]}
        />
      )}

      <Container>
        <section className="section" id="how">
          <div className="section-head">
            <div>
              <span className="eyebrow">How it works</span>
              <h2 className="display-lg" style={{ marginTop: 12 }}>
                Four steps.
              </h2>
            </div>
          </div>
          <InkRule thick />
          {STEPS.map(([title, body], i) => (
            <Reveal key={title} className="how-step" y={24}>
              <span className="how-num" aria-hidden="true">
                {i + 1}
              </span>
              <div>
                <h3 className="display-sm">{title}</h3>
                <p className="muted" style={{ marginTop: 6, maxWidth: '60ch' }}>
                  {body}
                </p>
              </div>
            </Reveal>
          ))}
        </section>

        <section className="section" style={{ paddingTop: 0 }}>
          <div className="section-head">
            <div>
              <span className="eyebrow">What you get</span>
              <h2 className="display-lg" style={{ marginTop: 12 }}>
                No black boxes.
              </h2>
            </div>
          </div>
          <Stagger className="grid grid-2" style={{ '--gap': '24px' }}>
            {FEATURES.map(({ icon: Icon, title, body, to }) => (
              <Card key={title} className="feature-card" hot>
                <div className="feature-icon">
                  <Icon size={26} aria-hidden="true" />
                </div>
                <h3 className="display-sm">{title}</h3>
                <p className="muted" style={{ marginTop: 8 }}>
                  {body}
                </p>
                {to && (
                  <p style={{ marginTop: 14 }}>
                    <Link className="link-plain" to={to}>
                      See the metrics
                    </Link>
                  </p>
                )}
              </Card>
            ))}
          </Stagger>
        </section>

        {stats && (
          <section className="section" style={{ paddingTop: 0 }}>
            <div className="section-head">
              <div>
                <span className="eyebrow">The catalog</span>
                <h2 className="display-lg" style={{ marginTop: 12 }}>
                  Pick a lane.
                </h2>
              </div>
              <Button to="/courses" iconRight={ArrowRight}>
                All {stats.count} courses
              </Button>
            </div>
            <SlideUp>
              <div className="cat-list">
                {Object.entries(stats.categories).map(([name, n]) => (
                  <Link key={name} to={`/courses?category=${encodeURIComponent(name)}`}>
                    <span className="badge">
                      {name} · {n}
                    </span>
                  </Link>
                ))}
              </div>
            </SlideUp>
            <div className="stats-strip" style={{ marginTop: 36 }}>
              <div>
                <span className="stat-label">Courses</span>
                <div className="stat-value">
                  <CountUp value={stats.count} />
                </div>
              </div>
              <div>
                <span className="stat-label">Hours of learning</span>
                <div className="stat-value">
                  <CountUp value={stats.hours} />
                </div>
              </div>
              <div>
                <span className="stat-label">Avg rating</span>
                <div className="stat-value">
                  <CountUp value={stats.rating} decimals={2} />
                </div>
              </div>
              <div>
                <span className="stat-label">Action types scored</span>
                <div className="stat-value">
                  <CountUp value={ACTION_COUNT} />
                </div>
              </div>
            </div>
          </section>
        )}

        <section className="section" style={{ paddingTop: 0 }}>
          <SlideUp>
            <div className="cta-block">
              <h2 className="display-lg">Start with a profile.</h2>
              <p className="lead" style={{ margin: '16px 0 28px' }}>
                Two minutes of questions, then a ranked list with the why next to every course.
              </p>
              <div className="row">
                <Button variant="secondary" size="lg" to={cta.to} iconRight={ArrowRight}>
                  {cta.label}
                </Button>
                <Button size="lg" to="/analytics" icon={BarChart3}>
                  See the model metrics
                </Button>
              </div>
            </div>
          </SlideUp>
        </section>
      </Container>
    </>
  )
}
