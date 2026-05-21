from sqlalchemy.orm import Session

from pman.models import Issue, Project, ProjectStatus, Risk, Task, WBSTask


class ProjectRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_project(self, name: str, description: str | None = None) -> Project:
        project = Project(name=name, description=description)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def get_project(self, project_id: int) -> Project | None:
        return self.session.query(Project).filter_by(id=project_id).first()

    def list_projects(self) -> list[Project]:
        return self.session.query(Project).order_by(Project.created_at.desc()).all()

    def update_project_status(self, project_id: int, status: ProjectStatus) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        project.status = status
        self.session.commit()
        return True

    def delete_project(self, project_id: int) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        self.session.delete(project)
        self.session.commit()
        return True

    def create_task(self, project_id: int, title: str, **kwargs) -> Task:
        task = Task(project_id=project_id, title=title, **kwargs)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def create_wbs_task(self, project_id: int, task_id: str, name: str, **kwargs) -> WBSTask:
        wbs = WBSTask(project_id=project_id, task_id=task_id, name=name, **kwargs)
        self.session.add(wbs)
        self.session.commit()
        self.session.refresh(wbs)
        return wbs

    def create_issue(self, project_id: int, title: str, **kwargs) -> Issue:
        issue = Issue(project_id=project_id, title=title, **kwargs)
        self.session.add(issue)
        self.session.commit()
        self.session.refresh(issue)
        return issue

    def create_risk(self, project_id: int, description: str, **kwargs) -> Risk:
        risk = Risk(project_id=project_id, description=description, **kwargs)
        self.session.add(risk)
        self.session.commit()
        self.session.refresh(risk)
        return risk
