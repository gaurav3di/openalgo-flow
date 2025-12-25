from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_admin
from app.core.rate_limit import limiter, API_LIMIT, EXECUTE_LIMIT, READ_LIMIT
from app.models.workflow import Workflow, WorkflowExecution
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListItem,
    WorkflowExecutionResponse,
    WorkflowExport,
    WorkflowImport
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=List[WorkflowListItem])
@limiter.limit(READ_LIMIT)
async def list_workflows(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """List all workflows"""
    result = await db.execute(
        select(Workflow).order_by(desc(Workflow.updated_at))
    )
    workflows = result.scalars().all()

    items = []
    for wf in workflows:
        # Get last execution status
        exec_result = await db.execute(
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == wf.id)
            .order_by(desc(WorkflowExecution.started_at))
            .limit(1)
        )
        last_exec = exec_result.scalar_one_or_none()

        items.append(WorkflowListItem(
            id=wf.id,
            name=wf.name,
            description=wf.description,
            is_active=wf.is_active,
            created_at=wf.created_at,
            updated_at=wf.updated_at,
            last_execution_status=last_exec.status if last_exec else None
        ))

    return items


@router.post("", response_model=WorkflowResponse)
@limiter.limit(API_LIMIT)
async def create_workflow(
    request: Request,
    workflow: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Create a new workflow"""
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description,
        nodes=workflow.nodes,
        edges=workflow.edges
    )
    db.add(db_workflow)
    await db.commit()
    await db.refresh(db_workflow)
    return db_workflow


@router.get("/{workflow_id}", response_model=WorkflowResponse)
@limiter.limit(READ_LIMIT)
async def get_workflow(
    request: Request,
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Get a workflow by ID"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
@limiter.limit(API_LIMIT)
async def update_workflow(
    request: Request,
    workflow_id: int,
    workflow_update: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Update a workflow"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow_update.name is not None:
        workflow.name = workflow_update.name
    if workflow_update.description is not None:
        workflow.description = workflow_update.description
    if workflow_update.nodes is not None:
        workflow.nodes = workflow_update.nodes
    if workflow_update.edges is not None:
        workflow.edges = workflow_update.edges

    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}")
@limiter.limit(API_LIMIT)
async def delete_workflow(
    request: Request,
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Delete a workflow"""
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Deactivate first if active
    if workflow.is_active:
        from app.services.executor import deactivate_workflow
        await deactivate_workflow(workflow_id, db)

    await db.delete(workflow)
    await db.commit()

    return {"status": "success", "message": "Workflow deleted"}


@router.post("/{workflow_id}/activate")
@limiter.limit(API_LIMIT)
async def activate_workflow(
    request: Request,
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Activate a workflow"""
    from app.services.executor import activate_workflow as activate
    result = await activate(workflow_id, db)
    return result


@router.post("/{workflow_id}/deactivate")
@limiter.limit(API_LIMIT)
async def deactivate_workflow(
    request: Request,
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Deactivate a workflow"""
    from app.services.executor import deactivate_workflow as deactivate
    result = await deactivate(workflow_id, db)
    return result


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
@limiter.limit(READ_LIMIT)
async def get_workflow_executions(
    request: Request,
    workflow_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Get execution history for a workflow"""
    result = await db.execute(
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(desc(WorkflowExecution.started_at))
        .limit(limit)
    )
    executions = result.scalars().all()
    return executions


@router.post("/{workflow_id}/execute")
@limiter.limit(EXECUTE_LIMIT)
async def execute_workflow_now(
    request: Request,
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Execute a workflow immediately"""
    from app.services.executor import execute_workflow
    result = await execute_workflow(workflow_id)
    return result


@router.get("/{workflow_id}/export", response_model=WorkflowExport)
@limiter.limit(READ_LIMIT)
async def export_workflow(
    request: Request,
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Export a workflow as JSON for sharing

    Returns the workflow in a format that can be imported by other users.
    Does not include execution history or schedule state.
    """
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowExport(
        version="1.0",
        name=workflow.name,
        description=workflow.description,
        nodes=workflow.nodes or [],
        edges=workflow.edges or [],
        exported_at=datetime.utcnow()
    )


@router.post("/import", response_model=WorkflowResponse)
@limiter.limit(API_LIMIT)
async def import_workflow(
    request: Request,
    workflow_data: WorkflowImport,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_current_admin)
):
    """Import a workflow from JSON

    Creates a new workflow from the provided data.
    The workflow will be inactive after import.
    """
    # Validate nodes have required structure
    for node in workflow_data.nodes:
        if "id" not in node or "type" not in node:
            raise HTTPException(
                status_code=400,
                detail="Invalid workflow: nodes must have 'id' and 'type' fields"
            )

    # Validate edges have required structure
    for edge in workflow_data.edges:
        if "source" not in edge or "target" not in edge:
            raise HTTPException(
                status_code=400,
                detail="Invalid workflow: edges must have 'source' and 'target' fields"
            )

    # Check if a workflow with the same name exists
    existing = await db.execute(
        select(Workflow).where(Workflow.name == workflow_data.name)
    )
    if existing.scalar_one_or_none():
        # Append a suffix to make it unique
        workflow_data.name = f"{workflow_data.name} (imported)"

    # Create the workflow
    db_workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        nodes=workflow_data.nodes,
        edges=workflow_data.edges,
        is_active=False  # Always import as inactive
    )
    db.add(db_workflow)
    await db.commit()
    await db.refresh(db_workflow)

    return db_workflow
