import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Plus,
  Loader2,
  Play,
  Pause,
  Trash2,
  MoreVertical,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Upload,
} from 'lucide-react'
import { workflowsApi, type WorkflowListItem, type WorkflowExportData } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

function StatusIcon({ status }: { status: string | null }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-buy" />
    case 'failed':
      return <XCircle className="h-4 w-4 text-sell" />
    case 'running':
      return <Loader2 className="h-4 w-4 animate-spin text-primary" />
    case 'pending':
      return <Clock className="h-4 w-4 text-muted-foreground" />
    default:
      return <AlertCircle className="h-4 w-4 text-muted-foreground" />
  }
}

function WorkflowCard({ workflow }: { workflow: WorkflowListItem }) {
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const activateMutation = useMutation({
    mutationFn: () => workflowsApi.activate(workflow.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast({ title: 'Workflow activated', variant: 'success' })
    },
    onError: (error: Error) => {
      toast({ title: 'Error', description: error.message, variant: 'destructive' })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: () => workflowsApi.deactivate(workflow.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast({ title: 'Workflow deactivated' })
    },
    onError: (error: Error) => {
      toast({ title: 'Error', description: error.message, variant: 'destructive' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => workflowsApi.delete(workflow.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      toast({ title: 'Workflow deleted' })
    },
    onError: (error: Error) => {
      toast({ title: 'Error', description: error.message, variant: 'destructive' })
    },
  })

  return (
    <Card
      className={cn(
        'group cursor-pointer transition-all duration-200 hover:border-primary/50',
        workflow.is_active && 'border-buy/30'
      )}
      onClick={() => navigate(`/editor/${workflow.id}`)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'status-dot',
                workflow.is_active ? 'active' : 'inactive'
              )}
            />
            <CardTitle className="text-base">{workflow.name}</CardTitle>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/editor/${workflow.id}`)
                }}
              >
                Edit
              </DropdownMenuItem>
              {workflow.is_active ? (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation()
                    deactivateMutation.mutate()
                  }}
                >
                  <Pause className="mr-2 h-4 w-4" />
                  Deactivate
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation()
                    activateMutation.mutate()
                  }}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Activate
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive"
                onClick={(e) => {
                  e.stopPropagation()
                  deleteMutation.mutate()
                }}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        {workflow.description && (
          <CardDescription className="line-clamp-2">
            {workflow.description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <StatusIcon status={workflow.last_execution_status} />
            <span>
              {workflow.last_execution_status
                ? `Last: ${workflow.last_execution_status}`
                : 'No executions'}
            </span>
          </div>
          <span className="text-xs text-muted-foreground">
            {new Date(workflow.updated_at).toLocaleDateString()}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

export function Dashboard() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [newWorkflowName, setNewWorkflowName] = useState('')
  const [importJson, setImportJson] = useState('')
  const [importError, setImportError] = useState<string | null>(null)

  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: workflowsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: workflowsApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      setIsCreateOpen(false)
      setNewWorkflowName('')
      navigate(`/editor/${data.id}`)
    },
    onError: (error: Error) => {
      toast({ title: 'Error', description: error.message, variant: 'destructive' })
    },
  })

  const importMutation = useMutation({
    mutationFn: workflowsApi.import,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      setIsImportOpen(false)
      setImportJson('')
      setImportError(null)
      toast({ title: 'Workflow imported', description: `Created "${data.name}"`, variant: 'success' })
      navigate(`/editor/${data.id}`)
    },
    onError: (error: Error) => {
      toast({ title: 'Import failed', description: error.message, variant: 'destructive' })
    },
  })

  const handleCreate = () => {
    if (!newWorkflowName.trim()) return
    createMutation.mutate({ name: newWorkflowName.trim() })
  }

  const handleImport = () => {
    setImportError(null)
    try {
      const parsed = JSON.parse(importJson) as WorkflowExportData
      // Validate basic structure
      if (!parsed.name || !Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
        setImportError('Invalid workflow format. Must have name, nodes, and edges.')
        return
      }
      importMutation.mutate(parsed)
    } catch {
      setImportError('Invalid JSON format. Please check the workflow data.')
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      setImportJson(content)
      setImportError(null)
    }
    reader.onerror = () => {
      setImportError('Failed to read file')
    }
    reader.readAsText(file)
  }

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Workflows</h1>
          <p className="text-muted-foreground">
            Create and manage your trading automations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setIsImportOpen(true)}>
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Button onClick={() => setIsCreateOpen(true)} className="btn-glow">
            <Plus className="mr-2 h-4 w-4" />
            New Workflow
          </Button>
        </div>
      </div>

      {workflows && workflows.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workflows.map((workflow) => (
            <WorkflowCard key={workflow.id} workflow={workflow} />
          ))}
        </div>
      ) : (
        <Card className="flex flex-col items-center justify-center py-16">
          <div className="mb-4 rounded-full bg-muted p-4">
            <Plus className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="mb-2 text-lg font-medium">No workflows yet</h3>
          <p className="mb-6 text-center text-sm text-muted-foreground">
            Create your first workflow to automate your trading
          </p>
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Workflow
          </Button>
        </Card>
      )}

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Workflow</DialogTitle>
            <DialogDescription>
              Give your workflow a name to get started
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Workflow Name</Label>
              <Input
                id="name"
                placeholder="e.g., Morning Order Automation"
                value={newWorkflowName}
                onChange={(e) => setNewWorkflowName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                autoFocus
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newWorkflowName.trim() || createMutation.isPending}
            >
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isImportOpen} onOpenChange={(open) => {
        setIsImportOpen(open)
        if (!open) {
          setImportJson('')
          setImportError(null)
        }
      }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Import Workflow</DialogTitle>
            <DialogDescription>
              Import a workflow from a JSON file or paste the JSON data
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="file">Upload File</Label>
              <Input
                id="file"
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="cursor-pointer"
              />
            </div>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  or paste JSON
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="json">Workflow JSON</Label>
              <Textarea
                id="json"
                placeholder='{"name": "My Workflow", "nodes": [...], "edges": [...]}'
                value={importJson}
                onChange={(e) => {
                  setImportJson(e.target.value)
                  setImportError(null)
                }}
                className="h-40 font-mono text-sm"
              />
              {importError && (
                <p className="text-sm text-destructive">{importError}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsImportOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={!importJson.trim() || importMutation.isPending}
            >
              {importMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Import
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
