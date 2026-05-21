import os
import shutil
import subprocess
from pathlib import Path


class EditorManager:
    def __init__(self, projects_dir: str | None = None):
        from pman.config import settings
        self.projects_dir = Path(projects_dir) if projects_dir else Path(settings.projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def open_editor(self, template: str, project_name: str) -> str:
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        draft_path = project_dir / "draft.md"
        draft_path.write_text(template, encoding="utf-8")

        editor = self._detect_editor()
        if editor == "cat":
            return template

        cmd = self._build_command(editor, str(draft_path))
        subprocess.run(cmd, check=False)

        content = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""
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
