"""Test per pman.models — ORM models e relazioni."""

from datetime import datetime, timezone

from pman.models import Project, ProjectStatus, Report, Sprint, Task, TaskSource, TaskStatus


class TestProject:
    def test_create_project_all_fields(self, db_session):
        p = Project(
            name="smot-pmanager",
            full_name="michele/smot-pmanager",
            description="AI project orchestration",
            status=ProjectStatus.ACTIVE,
            health_score=0.85,
        )
        db_session.add(p)
        db_session.commit()

        fetched = db_session.query(Project).filter_by(name="smot-pmanager").one()
        assert fetched.full_name == "michele/smot-pmanager"
        assert fetched.status == ProjectStatus.ACTIVE
        assert fetched.health_score == 0.85
        assert fetched.created_at is not None

    def test_project_default_status(self, db_session):
        p = Project(name="default-proj")
        db_session.add(p)
        db_session.commit()

        fetched = db_session.query(Project).one()
        assert fetched.status == ProjectStatus.ACTIVE
        assert fetched.health_score == 0.0


class TestTask:
    def test_create_task_all_fields(self, db_session):
        p = Project(name="proj-for-task")
        db_session.add(p)
        db_session.commit()

        t = Task(
            project_id=p.id,
            title="Implement auth",
            source=TaskSource.GITHUB,
            status=TaskStatus.TODO,
            priority=1,
            complexity=5,
            assigned_to="michele",
            labels='["backend","auth"]',
            ai_summary="Add JWT authentication",
        )
        db_session.add(t)
        db_session.commit()

        fetched = db_session.query(Task).one()
        assert fetched.title == "Implement auth"
        assert fetched.source == TaskSource.GITHUB
        assert fetched.status == TaskStatus.TODO
        assert fetched.priority == 1
        assert fetched.project.name == "proj-for-task"

    def test_task_defaults(self, db_session):
        t = Task(title="bare task")
        db_session.add(t)
        db_session.commit()

        fetched = db_session.query(Task).one()
        assert fetched.status == TaskStatus.BACKLOG
        assert fetched.source == TaskSource.MANUAL
        assert fetched.priority == 3


class TestSprint:
    def test_create_sprint(self, db_session):
        s = Sprint(
            name="Sprint 1",
            goal="MVP core features",
            status="planned",
            velocity=12.0,
        )
        db_session.add(s)
        db_session.commit()

        fetched = db_session.query(Sprint).one()
        assert fetched.name == "Sprint 1"
        assert fetched.goal == "MVP core features"
        assert fetched.velocity == 12.0
        assert fetched.created_at is not None


class TestReport:
    def test_create_report_with_project(self, db_session):
        p = Project(name="proj-for-report")
        db_session.add(p)
        db_session.commit()

        r = Report(
            type="velocity",
            project_id=p.id,
            content="Team velocity: 23 pts/sprint",
            ai_model="gemma4-dev",
        )
        db_session.add(r)
        db_session.commit()

        fetched = db_session.query(Report).one()
        assert fetched.type == "velocity"
        assert fetched.project.name == "proj-for-report"
        assert fetched.ai_model == "gemma4-dev"
        assert fetched.generated_at is not None
