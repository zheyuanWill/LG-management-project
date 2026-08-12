import { useState, useEffect } from 'react'
import { Save, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Select, type SelectOption } from '@/components/ui/Select'
import { useApiGet, useApiPatch } from '@/hooks/useApi'

const conclusionOptions: SelectOption[] = [
  { value: '', label: '请选择结论...' },
  { value: 'acceptable', label: '可承接' },
  { value: 'cautious', label: '谨慎承接' },
  { value: 'decline', label: '暂不承接' },
]

interface SurveyData {
  conclusion: string
  survey_detail: string
}

interface SurveyFormProps {
  projectId: string
}

export default function SurveyForm({ projectId }: SurveyFormProps) {
  const { data: survey, isLoading } = useApiGet<SurveyData>(
    `/brokerage/projects/${projectId}/surveys`
  )
  const patchSurvey = useApiPatch<SurveyData>(`/brokerage/projects/${projectId}/surveys`)

  const [conclusion, setConclusion] = useState('')
  const [details, setDetails] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    if (survey) {
      setConclusion(survey.conclusion || '')
      setDetails(survey.survey_detail || '')
    }
  }, [survey])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await patchSurvey.mutateAsync({ conclusion, survey_detail: details })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>背景调研</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">加载中...</p>
        ) : (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium">调研结论</label>
              <Select
                value={conclusion}
                onChange={(e) => setConclusion(e.target.value)}
                options={conclusionOptions}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">调研详情</label>
              <textarea
                className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="请输入调研详情,包括船东背景、船舶状况、市场分析等..."
                value={details}
                onChange={(e) => setDetails(e.target.value)}
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                保存
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}