from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from .render import render_rich
from .service import ConsoleService
from .timeutil import parse_user_datetime


class ConsoleTUI(App[None]):
    TITLE = "Local Console MVP"
    SUB_TITLE = "Manual planner + checklist printer"

    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

    #left, #right {
        width: 1fr;
        padding: 1;
    }

    .panel-title {
        margin-bottom: 1;
        text-style: bold;
    }

    #entries {
        height: 1fr;
        border: round $accent;
    }

    #form {
        border: round $surface;
        padding: 1;
        height: auto;
        margin-bottom: 1;
    }

    #preview {
        border: round $primary;
        padding: 1;
        height: 1fr;
        overflow-y: auto;
        background: white;
        color: black;
    }

    Input {
        margin-bottom: 1;
    }

    Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("p", "preview_selected", "Preview"),
        ("x", "print_selected", "Print"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, service: ConsoleService):
        super().__init__()
        self.service = service
        self.row_ids: list[int] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield Static("任务队列", classes="panel-title")
                yield DataTable(id="entries", zebra_stripes=True)
                with Horizontal():
                    yield Button("刷新", id="refresh")
                    yield Button("预览当前", id="preview-btn")
                    yield Button("立即打印", id="print-btn")
            with Vertical(id="right"):
                yield Static("新增条目", classes="panel-title")
                with Vertical(id="form"):
                    yield Input(placeholder="标题", id="title")
                    yield Input(
                        placeholder="触发时间，例如 2026-04-18 14:30",
                        id="due_at",
                    )
                    yield Input(placeholder="备注，可留空", id="notes")
                    yield Input(
                        placeholder="Checklist 项目，逗号分隔；留空则创建日程",
                        id="items",
                    )
                    yield Button("保存", id="save-entry")
                yield Static("预览", classes="panel-title")
                yield Static("选中左侧记录后，按预览或立即打印。", id="preview")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#entries", DataTable)
        table.add_columns("ID", "类型", "状态", "触发时间", "标题")
        self.refresh_table()

    def action_refresh(self) -> None:
        self.refresh_table()

    def action_preview_selected(self) -> None:
        self.update_preview()

    def action_print_selected(self) -> None:
        entry_id = self.selected_entry_id()
        if entry_id is None:
            self.notify("没有可打印的记录。")
            return
        preview_path = self.service.print_entry_now(entry_id)
        self.notify(f"已发送到打印机，预览图：{preview_path}")
        self.refresh_table()
        self.update_preview()

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "refresh":
            self.refresh_table()
        elif button_id == "preview-btn":
            self.update_preview()
        elif button_id == "print-btn":
            self.action_print_selected()
        elif button_id == "save-entry":
            self.save_entry()

    def refresh_table(self) -> None:
        table = self.query_one("#entries", DataTable)
        table.clear(columns=False)
        self.row_ids.clear()
        for entry in self.service.list_entries(limit=200):
            self.row_ids.append(entry.id)
            table.add_row(
                str(entry.id),
                entry.kind.value,
                entry.status.value,
                entry.due_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                entry.title,
            )
        if self.row_ids:
            table.cursor_coordinate = (0, 0)
            self.update_preview()
        else:
            self.query_one("#preview", Static).update("当前没有记录。")

    def selected_entry_id(self) -> int | None:
        if not self.row_ids:
            return None
        table = self.query_one("#entries", DataTable)
        row_index = max(0, min(table.cursor_row, len(self.row_ids) - 1))
        return self.row_ids[row_index]

    def update_preview(self) -> None:
        entry_id = self.selected_entry_id()
        preview = self.query_one("#preview", Static)
        if entry_id is None:
            preview.update("当前没有记录。")
            return
        artifact = self.service.preview_entry(entry_id)
        preview.update(
            render_rich(
                artifact.scene,
                self.service.settings,
                artifact.preview_path,
            )
        )

    def save_entry(self) -> None:
        title = self.query_one("#title", Input).value.strip()
        due_at_raw = self.query_one("#due_at", Input).value.strip()
        notes = self.query_one("#notes", Input).value.strip()
        items_raw = self.query_one("#items", Input).value.strip()
        if not title or not due_at_raw:
            self.notify("标题和触发时间不能为空。")
            return
        try:
            due_at = parse_user_datetime(due_at_raw)
            if items_raw:
                normalized = items_raw.replace("，", ",")
                items = [item.strip() for item in normalized.split(",") if item.strip()]
                self.service.create_checklist(
                    title=title,
                    due_at=due_at,
                    items=items,
                    notes=notes,
                )
            else:
                self.service.create_event(title=title, due_at=due_at, notes=notes)
        except Exception as exc:
            self.notify(str(exc))
            return

        for widget_id in ("title", "due_at", "notes", "items"):
            self.query_one(f"#{widget_id}", Input).value = ""
        self.notify("已保存。")
        self.refresh_table()
