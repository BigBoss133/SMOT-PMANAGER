import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pman.models import Base, Project, ProjectStatus
from pman.repository import ProjectRepository


def _db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


class TestProjectRepository:
    def test_create_project(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        project = repo.create_project("test-repo", "desc")
        assert project.id is not None
        assert project.name == "test-repo"

    def test_get_project(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        created = repo.create_project("get-test")
        fetched = repo.get_project(created.id)
        assert fetched is not None
        assert fetched.name == "get-test"

    def test_list_projects(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        repo.create_project("proj-1")
        repo.create_project("proj-2")
        projects = repo.list_projects()
        assert len(projects) == 2

    def test_update_status(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        project = repo.create_project("status-test")
        assert repo.update_project_status(project.id, ProjectStatus.ARCHIVED) is True
        fetched = repo.get_project(project.id)
        assert fetched.status == ProjectStatus.ARCHIVED

    def test_delete_project(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        project = repo.create_project("delete-test")
        assert repo.delete_project(project.id) is True
        assert repo.get_project(project.id) is None

    def test_create_wbs_task(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        project = repo.create_project("wbs-test")
        wbs = repo.create_wbs_task(project.id, "1.1", "Design", duration_days=5)
        assert wbs.task_id == "1.1"
        assert wbs.name == "Design"

    def test_create_issue(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        project = repo.create_project("issue-test")
        issue = repo.create_issue(project.id, "Bug found", severity="high")
        assert issue.title == "Bug found"
        assert issue.severity == "high"

    def test_create_risk(self):
        session = next(_db_session())
        repo = ProjectRepository(session)
        project = repo.create_project("risk-test")
        risk = repo.create_risk(project.id, "Budget overrun", probability="high")
        assert risk.description == "Budget overrun"
        assert risk.probability == "high"
