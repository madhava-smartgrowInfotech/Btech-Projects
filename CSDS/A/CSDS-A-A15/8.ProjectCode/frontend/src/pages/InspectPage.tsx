import { PageHeader } from '@/components/dashboard/PageHeader'
import { UploadCard } from '@/components/dashboard/UploadCard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'

export function InspectPage() {
  return (
    <div>
      <PageHeader title="New Inspection" description="Upload a surface image to run defect detection." />
      <div className="p-8 max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Upload surface image</CardTitle>
            <CardDescription>
              The model analyzes the image for six known defect categories and returns an
              explainable heatmap, root-cause narrative and severity rating.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <UploadCard />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
