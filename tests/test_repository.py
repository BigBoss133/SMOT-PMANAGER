import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from pman.models import Base, ProjectStatus
from pman.repository import ProjectRepository


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


class TestProjectRepository:
    @pytest.mark.asyncio
    async def test_create_project(self, db_session):
        repo = ProjectRepository(db_session)
        project = await repo.create_project("test-repo", "desc")
        assert project.id is not None
        assert project.name == "test-repo"

    @pytest.mark.asyncio
    async def test_get_project(self, db_session):
        repo = ProjectRepository(db_session)
        created = await repo.create_project("get-test")
        fetched = await repo.get_project(created.id)
        assert fetched is not None
        assert fetched.name == "get-test"

    @pytest.mark.asyncio
    async def test_list_projects(self, db_session):
        repo = ProjectRepository(db_session)
        await repo.create_project("proj-1")
        await repo.create_project("proj-2")
        projects = await repo.list_projects()
        assert len(projects) == 2

    @pytest.mark.asyncio
    async def test_update_status(self, db_session):
        repo = ProjectRepository(db_session)
        project = await repo.create_project("status-test")
        assert await repo.update_project_status(project.id, ProjectStatus.ARCHIVED) is True
        fetched = await repo.get_project(project.id)
        assert fetched.status == ProjectStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_delete_project(self, db_session):
        repo = ProjectRepository(db_session)
        project = await repo.create_project("delete-test")
        assert await repo.delete_project(project.id) is True
        assert await repo.get_project(project.id) is None

    @pytest.mark.asyncio
    async def test_create_wbs_task(self, db_session):
        repo = ProjectRepository(db_session)
        project = await repo.create_project("wbs-test")
        wbs = await repo.create_wbs_task(project.id, "1.1", "Design", duration_days=5)
        assert wbs.task_id == "1.1"
        assert wbs.name == "Design"

    @pytest.mark.asyncio
    async def test_create_issue(self, db_session):
        repo = ProjectRepository(db_session)
        project = await repo.create_project("issue-test")
        issue = await repo.create_issue(project.id, "Bug found", severity="high")
        assert issue.title == "Bug found"
        assert issue.severity == "high"

    @pytest.mark.asyncio
    async def test_create_risk(self, db_session):
        repo = ProjectRepository(db_session)
        project = await repo.create_project("risk-test")
        risk = await repo.create_risk(project.id, "Budget overrun", probability="high")
        assert risk.description == "Budget overrun"
        assert risk.probability == "high"
