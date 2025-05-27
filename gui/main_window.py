"""Repo Extractor GUI"""

from __future__ import annotations

import json
import time
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QRegularExpression
from PySide6.QtGui import QPalette, QColor, QIntValidator, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from repo_extractor import conf, extractor, schema

ISSUE_FIELDS = [
    "body",
    "closed_at",
    "created_at",
    "num_comments",
    "title",
    "userid",
    "userlogin",
]
COMMIT_FIELDS: list = ["author_name", "committer", "date", "files", "message", "sha"]
COMMENT_FIELDS: list = ["body", "userid", "userlogin"]
RANGE_DEFAULT: list = [0, 1]
CFG_DEFAULT: dict = {
    "repo": "",
    "auth_path": "",
    "output_path": "",
    "state": "open",
    "range": RANGE_DEFAULT,
    "issues": [],
    "commits": [],
    "comments": [],
}


class ExtractionWorker(QThread):
    """Runs the extractor in a separate thread so the UI stays responsive."""

    progress_changed = Signal(int)  # overall completion 0‑100
    status_changed = Signal(int, int, int)  # calls_left, cur_issue, total
    finished = Signal()

    def __init__(self, cfg_data: dict):
        super().__init__()
        self.cfg_data = cfg_data
        self._start_time: float | None = None

    def run(self) -> None:  # noqa: D401
        cfg_obj = conf.Cfg(self.cfg_data, schema.cfg_schema)

        print(self.cfg_data)

        print("\nInitializing extractor...")
        gh_ext = extractor.Extractor(cfg_obj)
        print(f"Extractor initialization complete!")

        print("\nRunning extractor...")
        gh_ext.get_repo_issues_data()
        print(f"Issue data complete!")

        print("\nExtraction complete!\n")


class FilePicker(QWidget):
    """A one-line widget that lets the user pick or create a file.

    Emits `pathChanged(str)` every time the selection changes.
    In save_mode it will touch the file on disk so it actually exists.
    """

    pathChanged = Signal(str)

    def __init__(
        self,
        parent=None,
        dialog_title: str = "Choose a file…",
        save_mode: bool = False,
        file_filter: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._dialog_title = dialog_title
        self._save_mode = save_mode
        self._filter = file_filter or ""

        self._le = QLineEdit(readOnly=True)
        self._btn = QPushButton("Browse…")
        self._btn.setFixedWidth(80)
        self._btn.clicked.connect(self._open_dialog)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._le, 1)
        lay.addWidget(self._btn)

    def path(self) -> str:
        return self._le.text()

    def setPath(self, path: str) -> None:
        self._le.setText(path)

    def _open_dialog(self) -> None:
        # start in the directory of the current path, or fallback to "."
        start_dir = Path(self._le.text() or ".").parent.as_posix()

        if self._save_mode:
            path, _ = QFileDialog.getSaveFileName(
                self,
                self._dialog_title,
                start_dir,
                self._filter,
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                self._dialog_title,
                start_dir,
                self._filter,
            )

        if not path:
            return

        # ensure `.json` extension if filter demands it
        if self._filter.lower().startswith("json") and not path.lower().endswith(
            ".json"
        ):
            path += ".json"

        # if save_mode, touch the file so it actually exists
        if self._save_mode:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).touch(exist_ok=True)
            except OSError:
                QMessageBox.warning(self, "Could not create file", path)

        # update display & emit
        self._le.setText(path)
        self.pathChanged.emit(path)


class NumberEdit(QLineEdit):
    """A QLineEdit that accepts only integers (optionally negative)
    and formats them with commas on focus-out.

    Emits `numberChanged(int)` whenever the numeric value changes.
    """

    numberChanged = Signal(int)

    def __init__(
        self,
        parent=None,
        allow_negative: bool = False,
        max_value: int | None = None,
    ) -> None:
        super().__init__(parent)
        self._allow_negative = allow_negative
        self._max_value = max_value
        self._last_value = 0
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._on_editing_finished)

    def _on_text_changed(self, text: str) -> None:
        plain = text.replace(",", "")
        if plain in ("", "-"):
            return
        try:
            val = int(plain)
        except ValueError:
            return
        if not self._allow_negative and val < 0:
            val = 0
        if self._max_value is not None and val > self._max_value:
            self.setText(f"{self._max_value}")
            return
        if val != self._last_value:
            self._last_value = val
            self.numberChanged.emit(val)

    def _on_editing_finished(self) -> None:
        # format with commas
        self.setText(f"{self._last_value:,}")

    def value(self) -> int:
        return self._last_value

    def setValue(self, val: int) -> None:
        if self._max_value is not None and val > self._max_value:
            val = self._max_value
        self._last_value = val
        self.setText(f"{val:,}")


class ConfigurationTab(QWidget):
    """Left: interactive form – Right: live JSON preview."""

    def __init__(self, main_window) -> None:  # noqa: D401
        super().__init__(main_window)
        self.main_window = main_window
        self.cfg_path: str | None = None
        self._dirty = False

        self.cfg_data = CFG_DEFAULT

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_form_pane())
        splitter.addWidget(self._build_json_pane())
        splitter.setSizes([380, 500])

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)

        self.btn_reset.clicked.connect(self._reset_form)
        self.btn_save.clicked.connect(self._save)
        self.btn_save_as.clicked.connect(self._save_as)
        self.btn_load.clicked.connect(self._load_config)

        self._refresh_json()

    def _set_valid_style(self, widget, ok: bool):
        """Apply or clear a red background on widget."""
        if ok:
            widget.setStyleSheet("")  # reset to default
        else:
            widget.setStyleSheet("background-color: #ffcccc;")  # light red

    def _validate(self):
        """Check each field, highlight invalid ones, and gate the Run button."""
        from pathlib import Path

        owner_ok = bool(self.le_owner.text()) and self.le_owner.hasAcceptableInput()
        self._set_valid_style(self.le_owner, owner_ok)

        # 2) Repo name: same
        repo_ok = (
            bool(self.le_repo_name.text()) and self.le_repo_name.hasAcceptableInput()
        )
        self._set_valid_style(self.le_repo_name, repo_ok)

        auth_path = self.fp_auth.path()
        auth_ok = bool(auth_path) and Path(auth_path).is_file()
        self._set_valid_style(self.fp_auth._le, auth_ok)

        out = self.fp_output.path()
        out_ok = bool(out) and out.lower().endswith(".json")
        self._set_valid_style(self.fp_output._le, out_ok)

        all_ok = owner_ok and repo_ok and auth_ok and out_ok
        self.main_window.ext_tab.btn_run.setEnabled(all_ok)

    def _mark_modified_display(self, filename: str) -> None:
        """Show a saved filename in red (dirty)."""
        # normal (non-italic) font
        font = self.le_cfg_file.font()
        font.setItalic(False)
        self.le_cfg_file.setFont(font)

        # red text
        pal = self.le_cfg_file.palette()
        pal.setColor(QPalette.ColorRole.Text, QColor("red"))
        self.le_cfg_file.setPalette(pal)

        self.le_cfg_file.setText(filename)

    def _mark_saved_display(self, filename: str) -> None:
        """Show a clean filename in default style."""
        self.le_cfg_file.setText(filename)
        font = self.le_cfg_file.font()
        font.setItalic(False)
        self.le_cfg_file.setFont(font)
        pal = self.le_cfg_file.palette()
        default = self.style().standardPalette().color(QPalette.ColorRole.Text)
        pal.setColor(QPalette.ColorRole.Text, default)
        self.le_cfg_file.setPalette(pal)

    def _update_repo_field(self) -> None:
        """Combine owner/name edits and update cfg_data['repo']."""
        owner = self.le_owner.text().strip()
        name = self.le_repo_name.text().strip()
        if owner or name:
            repo = f"{owner}/{name}"
        else:
            repo = ""
        self._update("repo", repo)

    def _is_form_valid(self) -> bool:
        if not (self.le_owner.hasAcceptableInput() and self.le_owner.text()):
            return False

        if not (self.le_repo_name.hasAcceptableInput() and self.le_repo_name.text()):
            return False

        auth = self.fp_auth.path()
        if not Path(auth).is_file():
            return False

        out_path = self.fp_output.path()
        if not out_path.lower().endswith(".json"):
            return False

        return True

    def _build_form_pane(self) -> QWidget:
        pane = QWidget()
        layout = QVBoxLayout(pane)

        # ─── Reset / Save / Save As / Load buttons ───────────────────────
        btn_row = QHBoxLayout()
        self.btn_reset = QPushButton("Clear Form")
        self.btn_save = QPushButton("Save")
        self.btn_save_as = QPushButton("Save As…")
        self.btn_load = QPushButton("Load")
        for b in (self.btn_reset, self.btn_save, self.btn_save_as, self.btn_load):
            btn_row.addWidget(b)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # ─── form starts here ──────────────────────────────────────────
        form = QFormLayout()
        layout.addLayout(form)
        layout.addStretch(1)

        # configuration file
        self.le_cfg_file = QLineEdit()
        self.le_cfg_file.setReadOnly(True)
        self.le_cfg_file.setText("")
        form.addRow("Configuration File:", self.le_cfg_file)

        # Repo split into owner / name
        self.le_owner = QLineEdit()
        self.le_repo_name = QLineEdit()
        self.le_owner.textChanged.connect(lambda _: self._update_repo_field())
        self.le_repo_name.textChanged.connect(lambda _: self._update_repo_field())
        self.le_owner.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"^[A-Za-z0-9-]+$"), self.le_owner
            )
        )

        repo_row = QHBoxLayout()
        repo_row.addWidget(self.le_owner, 1)
        repo_row.addWidget(QLabel("/"))
        repo_row.addWidget(self.le_repo_name, 1)
        form.addRow("Repo (owner/name):", repo_row)
        self.le_repo_name.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"^[A-Za-z0-9._-]+$"), self.le_repo_name
            )
        )

        # Auth FilePicker
        self.fp_auth = FilePicker(self, "Pick Personal Access Token file")
        self.fp_auth.pathChanged.connect(lambda p: self._update("auth_path", p))
        form.addRow("Personal Access Token File Path:", self.fp_auth)
        self.fp_auth._le.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"^.+\.txt$"), self.fp_auth._le
            )
        )

        # Output path
        self.fp_output = FilePicker(
            self,
            dialog_title="Save output JSON file as…",
            save_mode=False,
            file_filter="JSON files (*.json)",
        )
        self.fp_output.setPath(self.cfg_data["output_path"])
        self.fp_output.pathChanged.connect(lambda p: self._update("output_path", p))
        form.addRow("Output File Path:", self.fp_output)
        self.fp_output._le.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"^.+\.json$"), self.fp_output._le
            )
        )

        # — State combo
        self.cb_state = QComboBox()
        self.cb_state.addItems(["open", "closed"])
        self.cb_state.currentTextChanged.connect(lambda t: self._update("state", t))
        form.addRow("State:", self.cb_state)

        # --- range text fields with comma‐formatting -----------------
        self.le_start = NumberEdit(self, allow_negative=False, max_value=1_000_000)
        self.le_end = NumberEdit(self, allow_negative=False, max_value=1_000_000)
        self.le_start.setValue(1)
        self.le_end.setValue(1)

        range_row = QHBoxLayout()
        range_row.addWidget(self.le_start)
        range_row.addWidget(QLabel("to"))
        range_row.addWidget(self.le_end)
        form.addRow("Range:", range_row)

        for w in (
            self.le_owner,
            self.le_repo_name,
            self.le_start,
            self.le_end,
            self.fp_auth,
            self.fp_output,
        ):
            if isinstance(w, QLineEdit):
                w.textChanged.connect(self._validate)
            elif isinstance(w, NumberEdit):
                w.numberChanged.connect(self._validate)
            elif isinstance(w, FilePicker):
                w.pathChanged.connect(self._validate)

        # update config any time either number changes
        def _on_num_change(_: int) -> None:
            start = self.le_start.value()
            end = self.le_end.value()
            self._update("range", [start, end])
            if self.cfg_path:
                self._mark_modified_display(self.cfg_path)

        self.le_start.numberChanged.connect(_on_num_change)
        self.le_end.numberChanged.connect(_on_num_change)

        # — Check-list sections
        self.issues_box = self._make_checkbox_group(
            "Issues fields", ISSUE_FIELDS, "issues"
        )
        self.commits_box = self._make_checkbox_group(
            "Commit fields", COMMIT_FIELDS, "commits"
        )
        self.comments_box = self._make_checkbox_group(
            "Comment fields", COMMENT_FIELDS, "comments"
        )

        form.addRow(self.issues_box)
        form.addRow(self.commits_box)
        form.addRow(self.comments_box)

        return pane

    def _make_checkbox_group(
        self, title: str, items: list[str], cfg_key: str
    ) -> QGroupBox:
        box = QGroupBox(title)
        vbox = QVBoxLayout(box)
        for txt in items:
            cb = QCheckBox(txt)
            cb.stateChanged.connect(
                lambda _state, field=txt, key=cfg_key, cbx=cb: self._toggle_list_item(
                    key, field, cbx.isChecked()
                )
            )
            vbox.addWidget(cb)
        return box

    def _build_json_pane(self) -> QWidget:
        self.json_view = QTextEdit()
        self.json_view.setReadOnly(True)
        return self.json_view

    def _toggle_list_item(self, key: str, item: str, checked: bool) -> None:
        lst: list = self.cfg_data.setdefault(key, [])
        if checked and item not in lst:
            lst.append(item)
        elif not checked and item in lst:
            lst.remove(item)

        self._refresh_json()

        # mark dirty
        if self.cfg_path:
            self._mark_modified_display(self.cfg_path)
        else:
            self.le_cfg_file.setText("")

        self.main_window.setWindowModified(True)

    def _update(self, key: str, value) -> None:
        self.cfg_data[key] = value
        self._refresh_json()

        # mark dirty in the file-name display
        if self.cfg_path:
            self._mark_modified_display(self.cfg_path)
        else:
            self.le_cfg_file.setText("")

        self.main_window.setWindowModified(True)

    def _refresh_json(self) -> None:
        pretty = json.dumps(self.cfg_data, indent=2)
        self.json_view.setPlainText(pretty)
        self.main_window.on_config_updated(self.cfg_data)

    def _reload_form_from_dict(self) -> None:
        """Populate all widgets from `self.cfg_data`."""
        repo = self.cfg_data.get("repo", "")
        if "/" in repo:
            owner, name = repo.split("/", 1)
        else:
            owner, name = repo, ""
        self.le_owner.setText(owner)
        self.le_repo_name.setText(name)
        self.fp_auth.setPath(self.cfg_data.get("auth_path", ""))
        self.fp_output.setPath(self.cfg_data.get("output_path", ""))
        self.cb_state.setCurrentText(self.cfg_data.get("state", "open"))

        start, end = self.cfg_data.get("range", RANGE_DEFAULT)
        self.le_start.setValue(start)
        self.le_end.setValue(end)

        # check-box groups
        for key, box in [
            ("issues", self.issues_box),
            ("commits", self.commits_box),
            ("comments", self.comments_box),
        ]:
            wanted = set(self.cfg_data.get(key, []))
            for cb in box.findChildren(QCheckBox):
                cb.blockSignals(True)
                cb.setChecked(cb.text() in wanted)
                cb.blockSignals(False)

        self._refresh_json()

    # ----------------------------------------------------------------------
    def _save(self) -> None:
        """Save to last-loaded file, or fall back to Save As… if none."""
        if not self.cfg_path:
            return self._save_as()
        try:
            Path(self.cfg_path).write_text(
                json.dumps(self.cfg_data, indent=2) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            QMessageBox.critical(self, "Could not save file", str(exc))
            return
        # clear “dirty” state
        self._dirty = False
        self.main_window.setWindowModified(False)
        # update displayed config-filename
        self._mark_saved_display(self.cfg_path)
        self.main_window.statusBar().showMessage(f"Saved {self.cfg_path}", 2000)

    def _save_as(self) -> None:
        """Save current config under a new name."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save config as…",
            filter="JSON files (*.json)",
            selectedFilter="JSON files (*.json)",
            dir=self.cfg_path or "",
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            Path(path).write_text(json.dumps(self.cfg_data, indent=2) + "\n")
        except OSError as exc:
            QMessageBox.critical(self, "Could not write file", str(exc))
            return

        self.cfg_path = path
        self._dirty = False
        self.main_window.setWindowModified(False)
        self._mark_saved_display(self.cfg_path)
        self.main_window.statusBar().showMessage(f"Saved as {path}", 2000)

    # ----------------------------------------------------------------------
    def _load_config(self) -> None:
        """Load a .json from disk into the form."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open config", filter="JSON files (*.json)"
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.critical(self, "Could not load file", str(exc))
            return

        self.cfg_data = data
        self.cfg_path = path
        self._dirty = False
        self.main_window.setWindowModified(False)
        self._reload_form_from_dict()
        self._mark_saved_display(self.cfg_path)
        self.main_window.statusBar().showMessage(f"Loaded {path}", 2000)

    def _reset_form(self) -> None:
        """Clear back to built-in defaults and forget any filename."""
        self.cfg_data = CFG_DEFAULT
        self.cfg_path = None
        self._dirty = False
        self.main_window.setWindowModified(False)
        self.le_cfg_file.clear()
        self._reload_form_from_dict()
        self.main_window.statusBar().showMessage("Form reset to defaults", 2000)


class ExtractionTab(QWidget):
    def _update_runtime(self) -> None:
        if self._run_started_at is None:
            return
        elapsed = int(time.time() - self._run_started_at)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        self.lbl_runtime.setText(f"{h:02}:{m:02}:{s:02}")

    def __init__(self, main_window) -> None:  # noqa: D401
        super().__init__(main_window)
        self.main_window = main_window
        self.cfg_data: dict = CFG_DEFAULT

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(8, 8, 8, 8)

        # ---- Split‑pane with config preview (JSON) and extractor output
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.config_view = QTextEdit(readOnly=True)
        self.output_view = QTextEdit(readOnly=True)
        self.splitter.addWidget(self.config_view)
        self.splitter.addWidget(self.output_view)
        self.splitter.setSizes([350, 650])
        vlayout.addWidget(self.splitter, 1)

        # ---- Status box -------------------------------------------------
        status_box = QGroupBox("Current Extraction Status")
        self.lbl_calls_left = QLabel("–")
        self.lbl_issue_progress = QLabel("–")
        self.lbl_runtime = QLabel("–")
        status_layout = QFormLayout(status_box)
        status_layout.addRow("API calls left:", self.lbl_calls_left)
        status_layout.addRow("Issue:", self.lbl_issue_progress)
        status_layout.addRow("Runtime:", self.lbl_runtime)
        vlayout.addWidget(status_box)

        # ---- Bottom controls row ---------------------------------------
        controls = QHBoxLayout()
        self.btn_select_cfg = QPushButton("Select Config File…")
        self.btn_run = QPushButton("Run Extractor")
        self.btn_run.setEnabled(False)
        self.progress = QProgressBar(maximum=100)
        self.progress.setFixedWidth(260)

        controls.addWidget(self.btn_select_cfg)
        controls.addWidget(self.btn_run)
        controls.addStretch(1)
        controls.addWidget(self.progress)
        vlayout.addLayout(controls)

        # ---- Connections ----------------------------------------------
        self.btn_select_cfg.clicked.connect(self.select_config)
        self.btn_run.clicked.connect(self.start_extraction)

        # ---- Timer for runtime display ---------------------------------
        self.runtime_timer = QTimer(self)
        self.runtime_timer.setInterval(1000)
        self.runtime_timer.timeout.connect(self._update_runtime)

        # ---- State -----------------------------------------------------
        self.worker: ExtractionWorker | None = None
        self.cfg_path: str | None = None
        self._run_started_at: float | None = None

    def select_config(self) -> None:  # noqa: D401
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Config JSON", filter="JSON files (*.json)"
        )
        if path:
            self.cfg_path = path
            self.btn_run.setEnabled(True)
            self.config_view.setPlainText(Path(path).read_text())
            self.main_window.statusBar().showMessage(f"Loaded config: {path}")

    def _on_status_changed(self, calls_left: int, current: int, total: int) -> None:
        """Update the status labels as the worker emits progress."""
        self.lbl_calls_left.setText(str(calls_left))
        self.lbl_issue_progress.setText(f"{current}/{total}")

    def _on_finished(self) -> None:
        """Cleanup UI once extraction completes."""
        self.runtime_timer.stop()
        self.progress.setValue(100)
        self.btn_run.setEnabled(True)
        self.main_window.statusBar().showMessage("Extraction finished", 2000)

    def start_extraction(self) -> None:
        self.btn_run.setEnabled(False)
        self.progress.setValue(0)
        self.output_view.clear()
        self.lbl_calls_left.setText("–")
        self.lbl_issue_progress.setText("–")
        self.lbl_runtime.setText("00:00:00")

        self.worker = ExtractionWorker(self.cfg_data)
        self.worker.progress_changed.connect(self.progress.setValue)
        self.worker.status_changed.connect(self._on_status_changed)
        self.worker.finished.connect(self._on_finished)

        self._run_started_at = time.time()
        self.runtime_timer.start()
        self.worker.start()


class MainWindow(QMainWindow):
    """Top-level application window shown by gui/launcher.py."""

    def __init__(self) -> None:  # noqa: D401
        super().__init__()

        self.setWindowTitle("Repo Extractor[*]")
        self.setWindowModified(False)
        self.resize(1100, 700)

        # tab widget holds the two panels you already wrote
        tabs = QTabWidget(self)
        self.ext_tab = ExtractionTab(self)
        self.cfg_tab = ConfigurationTab(self)

        tabs.addTab(self.cfg_tab, "Configuration")
        tabs.addTab(self.ext_tab, "Extraction")

        self.setCentralWidget(tabs)

    # ---------- called by ConfigurationTab every time the form changes ----
    def on_config_updated(self, cfg: dict) -> None:
        """Synchronise live JSON with the Extraction tab."""
        pretty = json.dumps(cfg, indent=2)
        self.ext_tab.config_view.setPlainText(pretty)
        self.ext_tab.cfg_data = dict(cfg)
