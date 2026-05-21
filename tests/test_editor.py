import os
import tempfile
from pathlib import Path

from pman.editor import EditorManager


class TestOpenEditor:
    def test_cat_editor_returns_template(self):
        manager = EditorManager(projects_dir=tempfile.mkdtemp())
        os.environ["EDITOR"] = "cat"
        result = manager.open_editor("# Hello\nWorld", "test-cat")
        assert "# Hello" in result
        assert "World" in result

    def test_file_created(self):
        tmp = tempfile.mkdtemp()
        manager = EditorManager(projects_dir=tmp)
        os.environ["EDITOR"] = "cat"
        manager.open_editor("# Test", "test-file")
        draft = Path(tmp) / "test-file" / "draft.md"
        assert draft.exists()
        assert draft.read_text() == "# Test"

    def test_empty_content_handled(self):
        tmp = tempfile.mkdtemp()
        manager = EditorManager(projects_dir=tmp)
        os.environ["EDITOR"] = "cp /dev/null"
        result = manager.open_editor("# Template", "test-empty")
        assert result == ""


class TestSaveSnapshot:
    def test_roundtrip(self):
        tmp = tempfile.mkdtemp()
        manager = EditorManager(projects_dir=tmp)
        manager.save_snapshot("v1 content", "snapshot-test", 1)
        latest = manager.get_latest_content("snapshot-test")
        assert latest == "v1 content"

    def test_latest_returns_none_for_missing(self):
        tmp = tempfile.mkdtemp()
        manager = EditorManager(projects_dir=tmp)
        assert manager.get_latest_content("nonexistent") is None

    def test_snapshot_numbered(self):
        tmp = tempfile.mkdtemp()
        manager = EditorManager(projects_dir=tmp)
        path = manager.save_snapshot("v2", "snap-num", 2)
        assert "draft_v2.md" in str(path)
