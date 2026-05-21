from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pman.models import Issue, Project, ProjectStatus, Risk, Task, WBSTask


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_project(
        self, name: str, description: str | None = None
    ) -> Project:
        project = Project(name=name, description=description)
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_project(self, project_id: int) -> Project | None:
        result = await self.session.execute(
            select(Project).filter_by(id=project_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(self) -> list[Project]:
        result = await self.session.execute(
            select(Project).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_project_status(
        self, project_id: int, status: ProjectStatus
    ) -> bool:
        project = await self.get_project(project_id)
        if not project:
            return False
        project.status = status
        await self.session.commit()
        return True

    async def delete_project(self, project_id: int) -> bool:
        project = await self.get_project(project_id)
        if not project:
            return False
        await self.session.delete(project)
        await self.session.commit()
        return True

    async def create_task(
        self, project_id: int, title: str, **kwargs
    ) -> Task:
        task = Task(project_id=project_id, title=title, **kwargs)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def create_wbs_task(
        self, project_id: int, task_id: str, name: str, **kwargs
    ) -> WBSTask:
        wbs = WBSTask(project_id=project_id, task_id=task_id, name=name, **kwargs)
        self.session.add(wbs)
        await self.session.commit()
        await self.session.refresh(wbs)
        return wbs

    async def create_issue(
        self, project_id: int, title: str, **kwargs
    ) -> Issue:
        issue = Issue(project_id=project_id, title=title, **kwargs)
        self.session.add(issue)
        await self.session.commit()
        await self.session.refresh(issue)
        return issue

    async def create_risk(
        self, project_id: int, description: str, **kwargs
    ) -> Risk:
        risk = Risk(project_id=project_id, description=description, **kwargs)
        self.session.add(risk)
        await self.session.commit()
        await self.session.refresh(risk)
        return risk
