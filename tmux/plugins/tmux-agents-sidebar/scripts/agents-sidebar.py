#!/usr/bin/env python3
import argparse
import os
import re
import select
import signal
import subprocess
import sys
import termios
import time
import tty
from dataclasses import dataclass
from typing import List, Optional, Tuple

INPUT_POLL_INTERVAL = 0.03
SNAPSHOT_INTERVAL = 0.15

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
FG_CYAN = "\033[36m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[38;5;226m"
FG_RED = "\033[31m"
FG_GRAY = "\033[90m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_SCREEN = "\033[2J"
HOME = "\033[H"
CLEAR_LINE = "\033[2K"
ENABLE_MOUSE = "\033[?1000h\033[?1006h"
DISABLE_MOUSE = "\033[?1000l\033[?1006l"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class SidebarError(RuntimeError):
    pass


@dataclass(frozen=True)
class Agent:
    name: str
    pane_id: str
    window_id: str
    window_name: str
    folder: str
    branch: str
    active: bool


@dataclass(frozen=True)
class SidebarState:
    mode: str
    active_name: str
    last_active_name: str
    sidebar_pane: str
    focus_pane: str
    epoch: int
    width: int
    height: int
    agents: List[Agent]


class TerminalController:
    def __init__(self) -> None:
        self.fd = sys.stdin.fileno()
        self.original = termios.tcgetattr(self.fd)

    def __enter__(self) -> "TerminalController":
        tty.setcbreak(self.fd)
        sys.stdout.write(HIDE_CURSOR + ENABLE_MOUSE + HOME)
        sys.stdout.flush()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.original)
        sys.stdout.write(DISABLE_MOUSE + SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()


class SidebarApp:
    def __init__(self, session: str, controller: str) -> None:
        self.session = session
        self.controller = controller
        self.state: Optional[SidebarState] = None
        self.selected_index = 0
        self.last_lines: List[str] = []
        self.redraw_full = True
        self.force_snapshot = True
        self.last_snapshot_at = 0.0
        self.message = ""
        self.message_until = 0.0

    def run_controller(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([self.controller, *args], capture_output=True, text=True)

    def set_message(self, message: str, seconds: float = 1.5) -> None:
        self.message = message
        self.message_until = time.time() + seconds

    def clear_message_if_expired(self) -> None:
        if self.message and time.time() >= self.message_until:
            self.message = ""

    def snapshot_due(self) -> bool:
        return self.force_snapshot or self.state is None or (time.time() - self.last_snapshot_at) >= SNAPSHOT_INTERVAL

    def fetch_snapshot(self) -> SidebarState:
        proc = self.run_controller("snapshot")
        if proc.returncode != 0:
            raise SidebarError(proc.stderr.strip() or proc.stdout.strip() or "failed to fetch sidebar snapshot")

        mode = "unknown"
        active_name = ""
        last_active_name = ""
        sidebar_pane = ""
        focus_pane = ""
        epoch = 0
        width = 0
        height = 0
        agents: List[Agent] = []

        for raw_line in proc.stdout.splitlines():
            if not raw_line:
                continue
            parts = raw_line.split("\t")
            kind = parts[0]
            if kind == "mode":
                mode = parts[1] if len(parts) > 1 else "unknown"
            elif kind == "active_name":
                active_name = parts[1] if len(parts) > 1 else ""
            elif kind == "last_active_name":
                last_active_name = parts[1] if len(parts) > 1 else ""
            elif kind == "sidebar_pane":
                sidebar_pane = parts[1] if len(parts) > 1 else ""
            elif kind == "focus_pane":
                focus_pane = parts[1] if len(parts) > 1 else ""
            elif kind == "epoch":
                epoch = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            elif kind == "size":
                width = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                height = int(parts[2]) if len(parts) > 2 and parts[2] else 0
            elif kind == "agent" and len(parts) >= 7:
                name, pane_id, window_id, window_name, folder, branch = parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
                agents.append(
                    Agent(
                        name=name,
                        pane_id=pane_id,
                        window_id=window_id,
                        window_name=window_name,
                        folder=folder,
                        branch=branch,
                        active=name == active_name,
                    )
                )

        return SidebarState(
            mode=mode,
            active_name=active_name,
            last_active_name=last_active_name,
            sidebar_pane=sidebar_pane,
            focus_pane=focus_pane,
            epoch=epoch,
            width=width,
            height=height,
            agents=agents,
        )

    def sync_selection(self, previous: Optional[SidebarState], current: SidebarState) -> None:
        if not current.agents:
            self.selected_index = 0
            return

        names = [agent.name for agent in current.agents]
        if self.selected_index >= len(names):
            self.selected_index = len(names) - 1

        if previous is None:
            if current.active_name in names:
                self.selected_index = names.index(current.active_name)
            return

        if previous.active_name != current.active_name and current.active_name in names:
            self.selected_index = names.index(current.active_name)

    def maybe_refresh_snapshot(self) -> None:
        if not self.snapshot_due():
            return

        previous = self.state
        current = self.fetch_snapshot()
        self.last_snapshot_at = time.time()
        self.force_snapshot = False

        if previous is None or previous.width != current.width or previous.height != current.height:
            self.redraw_full = True

        self.sync_selection(previous, current)
        self.state = current

    def row_window(self, state: SidebarState) -> Tuple[int, int, List[Agent]]:
        rows_available = max(1, state.height - 8)
        start = 0
        if self.selected_index >= rows_available:
            start = self.selected_index - rows_available + 1
        visible = state.agents[start : start + rows_available]
        return start, rows_available, visible

    def crop_plain(self, text: str, width: int) -> str:
        if width <= 0:
            return ""
        if len(text) <= width:
            return text
        if width == 1:
            return text[:1]
        return text[: width - 1] + "…"

    def pad_plain(self, text: str, width: int) -> str:
        cropped = self.crop_plain(text, width)
        return cropped + (" " * max(0, width - len(cropped)))

    def render_line(self, plain: str, *styles: str) -> str:
        return "".join(styles) + plain + RESET

    def marker(self, agent: Agent) -> Tuple[str, str]:
        if agent.active:
            return "X", FG_CYAN
        return "", FG_GRAY

    def visible_len(self, text: str) -> int:
        return len(ANSI_RE.sub("", text))

    def pad_ansi(self, text: str, width: int) -> str:
        plain_len = self.visible_len(text)
        if plain_len >= width:
            return text
        return text + (" " * (width - plain_len))

    def agent_row(self, index: int, agent: Agent, selected: bool, width: int) -> str:
        folder = agent.folder or agent.name
        branch = agent.branch.strip()
        active_suffix = " - X" if agent.active else ""
        base_plain = f" {index:>2} {folder}"
        branch_plain = f" - ({branch})" if branch else ""
        full_plain = f"{base_plain}{branch_plain}{active_suffix}"

        if len(full_plain) > width:
            plain = self.pad_plain(full_plain, width)
            style_parts: List[str] = []
            if selected:
                style_parts.extend([FG_CYAN, BOLD])
            elif agent.active:
                style_parts.append(BOLD)
            return self.render_line(plain, *style_parts)

        parts: List[str] = []
        if selected:
            parts.extend([FG_CYAN, BOLD])
        else:
            parts.extend([DIM, f" {index:>2} ", RESET])

        if selected:
            parts.append(f" {index:>2} ")
        parts.append(BOLD if (agent.active or selected) else "")
        parts.append(folder)
        if branch:
            parts.extend([DIM, " - ", FG_YELLOW, f"({branch})", RESET])
        if agent.active:
            parts.extend([DIM, " - ", FG_GREEN, BOLD, "X", RESET])
        elif selected:
            parts.append(RESET)
        return self.pad_ansi("".join(parts), width)

    def build_lines(self, state: SidebarState) -> List[str]:
        width = max(20, state.width)
        height = max(8, state.height)
        separator = "─" * width
        lines: List[str] = []

        lines.append(self.render_line(self.pad_plain(" Agents ", width), BOLD, FG_CYAN))
        lines.append(self.render_line(self.pad_plain(separator, width), DIM))

        start, rows_available, visible_agents = self.row_window(state)
        for offset, agent in enumerate(visible_agents, start=start):
            lines.append(self.agent_row(offset + 1, agent, offset == self.selected_index, width))

        while len(lines) < 2 + rows_available:
            lines.append(self.pad_plain("", width))

        lines.append(self.render_line(self.pad_plain(separator, width), DIM))
        lines.append(self.render_line(self.pad_plain(f" last  {state.last_active_name or '—'}", width), DIM))
        lines.append(self.render_line(self.pad_plain(f" mode  {state.mode}", width), DIM))
        lines.append(self.render_line(self.pad_plain(" j/k move  enter switch", width), FG_GRAY))
        lines.append(self.render_line(self.pad_plain(" 1-9 direct  esc focus", width), FG_GRAY))

        if self.message:
            lines.append(self.render_line(self.pad_plain(f" {self.message}", width), FG_YELLOW, BOLD))
        else:
            lines.append(self.pad_plain("", width))

        if len(lines) > height:
            lines = lines[:height]
        while len(lines) < height:
            lines.append(self.pad_plain("", width))
        return lines

    def render(self) -> None:
        if self.state is None:
            return
        lines = self.build_lines(self.state)
        out: List[str] = []

        if self.redraw_full or len(self.last_lines) != len(lines):
            out.append(HOME + CLEAR_SCREEN)
            self.last_lines = [""] * len(lines)
            self.redraw_full = False

        for row, line in enumerate(lines, start=1):
            if row - 1 >= len(self.last_lines) or self.last_lines[row - 1] != line:
                out.append(f"\033[{row};1H{CLEAR_LINE}{line}")

        if out:
            sys.stdout.write("".join(out))
            sys.stdout.flush()
            self.last_lines = list(lines)

    def focus_name(self, name: str) -> None:
        proc = self.run_controller("focus", name)
        if proc.returncode != 0:
            raise SidebarError(proc.stderr.strip() or proc.stdout.strip() or f"failed to focus {name}")
        self.force_snapshot = True
        self.set_message(f"focused {name}", 1.0)

    def controller_command(self, command: str, error_message: str) -> None:
        proc = self.run_controller(command)
        if proc.returncode != 0:
            raise SidebarError(proc.stderr.strip() or proc.stdout.strip() or error_message)
        self.force_snapshot = True

    def move_selection(self, delta: int) -> None:
        if self.state is None or not self.state.agents:
            return
        self.selected_index = (self.selected_index + delta) % len(self.state.agents)

    def selected_agent(self) -> Optional[Agent]:
        if self.state is None or not self.state.agents:
            return None
        return self.state.agents[self.selected_index]

    def read_key(self, timeout: float) -> Optional[str]:
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if not ready:
            return None

        data = os.read(sys.stdin.fileno(), 1)
        if not data:
            return None

        if data == b"\x1b":
            parts = [data]
            while True:
                more, _, _ = select.select([sys.stdin], [], [], 0.005)
                if not more:
                    break
                chunk = os.read(sys.stdin.fileno(), 32)
                if not chunk:
                    break
                parts.append(chunk)
                if chunk.endswith((b"M", b"m", b"A", b"B", b"C", b"D", b"~")):
                    break
            seq = b"".join(parts)
            if seq.startswith(b"\x1b[A"):
                return "up"
            if seq.startswith(b"\x1b[B"):
                return "down"
            if seq.startswith(b"\x1b[<"):
                return seq.decode("utf-8", "ignore")
            return "escape"

        if data in (b"\r", b"\n"):
            return "enter"
        if data == b"\t":
            return "tab"
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def handle_mouse(self, sequence: str) -> bool:
        if self.state is None:
            return False
        match = re.match(r"\x1b\[<([0-9]+);([0-9]+);([0-9]+)([Mm])", sequence)
        if not match:
            return False
        button = int(match.group(1))
        x = int(match.group(2))
        y = int(match.group(3))
        kind = match.group(4)
        _ = x

        if kind != "M":
            return True

        if button == 64:
            self.move_selection(-1)
            return True
        if button == 65:
            self.move_selection(1)
            return True

        start, _rows_available, visible_agents = self.row_window(self.state)
        agent_row_start = 3
        if 0 <= button <= 2 and agent_row_start <= y < agent_row_start + len(visible_agents):
            index = start + (y - agent_row_start)
            if 0 <= index < len(self.state.agents):
                self.selected_index = index
                self.focus_name(self.state.agents[index].name)
            return True
        return False

    def handle_key(self, key: str) -> None:
        if self.state is None:
            return
        if key == "up" or key == "k":
            self.move_selection(-1)
            return
        if key == "down" or key == "j":
            self.move_selection(1)
            return
        if key == "g":
            self.selected_index = 0
            return
        if key == "G" and self.state.agents:
            self.selected_index = len(self.state.agents) - 1
            return
        if key == "enter":
            agent = self.selected_agent()
            if agent is not None:
                self.focus_name(agent.name)
            return
        if key in ("escape", "q"):
            self.controller_command("focus-right", "failed to focus active pane")
            self.set_message("focused active pane", 1.0)
            return
        if key == "r":
            self.force_snapshot = True
            self.set_message("refreshed", 0.8)
            return
        if key == "n":
            self.controller_command("next", "failed to focus next agent")
            return
        if key == "p":
            self.controller_command("prev", "failed to focus previous agent")
            return
        if key and key.isdigit() and key != "0":
            index = int(key) - 1
            if 0 <= index < len(self.state.agents):
                self.selected_index = index
                self.focus_name(self.state.agents[index].name)
            else:
                self.set_message(f"no agent {key}", 1.2)
            return
        if key.startswith("\x1b[<"):
            self.handle_mouse(key)

    def run(self) -> int:
        signal.signal(signal.SIGWINCH, lambda *_args: setattr(self, "redraw_full", True))
        with TerminalController():
            while True:
                self.clear_message_if_expired()
                self.maybe_refresh_snapshot()
                self.render()
                key = self.read_key(INPUT_POLL_INTERVAL)
                if key is None:
                    continue
                try:
                    self.handle_key(key)
                except SidebarError as error:
                    self.set_message(str(error), 2.0)
                self.render()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--controller", required=True)
    args = parser.parse_args()

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("agents-sidebar: stdin/stdout must be a tty", file=sys.stderr)
        return 1

    try:
        return SidebarApp(args.session, args.controller).run()
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(f"agents-sidebar: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
