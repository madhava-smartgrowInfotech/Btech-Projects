import { ArrowLeft } from 'lucide-react'
import { Button, Container } from '../components/ui'
import { MaskHeadline, PageTransition } from '../components/motion'

export default function NotFound() {
  return (
    <PageTransition>
      <Container style={{ padding: '72px 16px 96px' }}>
        <span className="eyebrow">Error 404</span>
        <MaskHeadline className="display-xl" lines={['Not', 'on the', 'register.']} />
        <p className="lead muted" style={{ margin: '20px 0 28px' }}>
          This page does not exist. If you followed a session link, ask your faculty to share it again.
        </p>
        <Button variant="primary" size="lg" to="/" icon={ArrowLeft}>
          Back to home
        </Button>
      </Container>
    </PageTransition>
  )
}
