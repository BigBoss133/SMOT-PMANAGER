import os
import shutil
import subprocess
import time
from pathlib import Path


class EditorManager:
    AUTOSAVE_INTERVAL = 30  # seconds

    def __init__(self, projects_dir: str | None = None):
        from pman.config import settings
        self.projects_dir = Path(projects_dir) if projects_dir else Path(settings.projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _autosave_path(self, project_name: str) -> Path:
        return self.projects_dir / project_name / ".draft_autosave.md"

    def save_autorecovery(self, content: str, project_name: str) -> Path:
        """Save a hidden auto-recovery file."""
        path = self._autosave_path(project_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def has_recovery(self, project_name: str) -> bool:
        """Check if an auto-recovery file exists and is recent."""
        path = self._autosave_path(project_name)
        if not path.exists():
            return False
        # Recovery is valid if file is younger than 1 hour
        age = time.time() - path.stat().st_mtime
        return age < 3600

    def recover(self, project_name: str) -> str | None:
        """Return recovery content if available."""
        path = self._autosave_path(project_name)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def clear_recovery(self, project_name: str) -> None:
        """Remove auto-recovery file after successful save."""
        path = self._autosave_path(project_name)
        if path.exists():
            path.unlink()

    def open_editor(self, template: str, project_name: str) -> str:
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        draft_path = project_dir / "draft.md"
        draft_path.write_text(template, encoding="utf-8")

        # Save auto-recovery before opening editor
        self.save_autorecovery(template, project_name)

        editor = self._detect_editor()
        if editor == "cat":
            self.clear_recovery(project_name)
            return template

        cmd = self._build_command(editor, str(draft_path))
        subprocess.run(cmd, check=False)

        content = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""
        self.clear_recovery(project_name)
        return content

    def _detect_editor(self) -> str:
        env_editor = os.environ.get("EDITOR", "")
        if env_editor:
            return env_editor

        import platform
        system = platform.system()
        if system == "Windows":
            for candidate in ["code --wait", "notepad"]:
                if shutil.which(candidate.split()[0]):
                    return candidate
            return "notepad"

        for candidate in ["nano", "vim", "vi"]:
            if shutil.which(candidate):
                return candidate
        return "cat"

    def _build_command(self, editor: str, file_path: str) -> list[str]:
        if " " in editor:
            return editor.split() + [file_path]
        return [editor, file_path]

    def save_snapshot(self, content: str, project_name: str, iteration: int) -> Path:
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = project_dir / f"draft_v{iteration}.md"
        snapshot_path.write_text(content, encoding="utf-8")
        return snapshot_path

    def get_latest_content(self, project_name: str) -> str | None:
        project_dir = self.projects_dir / project_name
        draft_path = project_dir / "draft.md"
        if draft_path.exists():
            return draft_path.read_text(encoding="utf-8")
        snapshots = sorted(project_dir.glob("draft_v*.md"))
        if snapshots:
            return snapshots[-1].read_text(encoding="utf-8")
        return None

    def get_next_iteration(self, project_name: str) -> int:
        project_dir = self.projects_dir / project_name
        snapshots = list(project_dir.glob("draft_v*.md"))
        if not snapshots:
            return 1
        max_iter = max(int(p.stem.split("_v")[1]) for p in snapshots)
        return max_iter + 1
