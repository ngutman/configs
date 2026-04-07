import type { ExtensionAPI, ExtensionContext } from "@mariozechner/pi-coding-agent";
import { basename } from "node:path";

type SidebarStatus = "idle" | "running" | "tool" | "done" | "unknown";

const paneId = process.env.TMUX_PANE;

export default function agentsSidebarStatusExtension(pi: ExtensionAPI) {
	let sessionId: string | undefined;
	let currentStatus: SidebarStatus = "idle";
	let currentStatusText = "";

	const inTmux = Boolean(paneId);

	async function tmux(args: string[]): Promise<string | undefined> {
		if (!inTmux) return undefined;
		const result = await pi.exec("tmux", args);
		if (result.code !== 0) return undefined;
		return result.stdout.trim();
	}

	async function ensureSessionId(): Promise<string | undefined> {
		if (!inTmux) return undefined;
		if (sessionId) return sessionId;
		sessionId = await tmux(["display-message", "-p", "-t", paneId!, "#{session_id}"]);
		return sessionId;
	}

	function paneOptionName(suffix: string): string {
		return `@agents_sidebar_${suffix}_${paneId!.slice(1)}`;
	}

	async function setSessionOption(name: string, value?: string): Promise<void> {
		const sid = await ensureSessionId();
		if (!sid) return;
		if (value === undefined || value === "") {
			await pi.exec("tmux", ["set-option", "-qu", "-t", sid, name]);
			return;
		}
		await pi.exec("tmux", ["set-option", "-q", "-t", sid, name, value]);
	}

	async function bumpEpoch(): Promise<void> {
		await setSessionOption("@agents_sidebar_epoch", `${Date.now()}`);
	}

	async function setPaneMeta(suffix: string, value?: string): Promise<void> {
		await setSessionOption(paneOptionName(suffix), value);
	}

	function renderFooterStatus(ctx: ExtensionContext, status: SidebarStatus, statusText = ""): void {
		if (!ctx.hasUI) return;
		const theme = ctx.ui.theme;
		let text = theme.fg("dim", "π sidebar ");
		if (status === "tool") {
			text += theme.fg("warning", "⚙");
			text += theme.fg("dim", ` ${statusText || "tool"}`);
		} else if (status === "running") {
			text += theme.fg("accent", "…");
			text += theme.fg("dim", " running");
		} else if (status === "done") {
			text += theme.fg("success", "✓");
			text += theme.fg("dim", " done");
		} else if (status === "idle") {
			text += theme.fg("dim", "idle");
		} else {
			text += theme.fg("warning", "?");
			text += theme.fg("dim", " unknown");
		}
		ctx.ui.setStatus("agents-sidebar", text);
	}

	async function seedLabelIfMissing(ctx: ExtensionContext): Promise<void> {
		const sid = await ensureSessionId();
		if (!sid) return;
		const existing = await tmux(["show-option", "-qv", "-t", sid, paneOptionName("name")]);
		if (existing) return;

		const title = await tmux(["display-message", "-p", "-t", paneId!, "#{pane_title}"]);
		if (title?.startsWith("π - ")) {
			await setPaneMeta("name", title.slice(4));
			return;
		}

		const cwdBase = basename(ctx.cwd || "");
		if (cwdBase) {
			await setPaneMeta("name", cwdBase);
		}
	}

	async function updateStatus(ctx: ExtensionContext, status: SidebarStatus, statusText = ""): Promise<void> {
		if (!inTmux) return;
		currentStatus = status;
		currentStatusText = statusText;
		await setPaneMeta("kind", "agent");
		await setPaneMeta("provider", "pi");
		await setPaneMeta("status", status);
		await setPaneMeta("status_text", status === "tool" ? statusText : undefined);
		await setPaneMeta("last_done", status === "done" ? `${Math.floor(Date.now() / 1000)}` : undefined);
		await bumpEpoch();
		renderFooterStatus(ctx, status, statusText);
	}

	if (!inTmux) return;

	pi.on("session_start", async (_event, ctx) => {
		await ensureSessionId();
		await seedLabelIfMissing(ctx);
		await updateStatus(ctx, "idle");
	});

	pi.on("agent_start", async (_event, ctx) => {
		await updateStatus(ctx, "running");
	});

	pi.on("tool_execution_start", async (event, ctx) => {
		await updateStatus(ctx, "tool", event.toolName);
	});

	pi.on("tool_execution_end", async (_event, ctx) => {
		await updateStatus(ctx, "running");
	});

	pi.on("turn_end", async (_event, ctx) => {
		if (currentStatus !== "done") {
			await updateStatus(ctx, "running", currentStatusText);
		}
	});

	pi.on("agent_end", async (_event, ctx) => {
		await updateStatus(ctx, "done");
	});

	pi.on("session_shutdown", async (_event, ctx) => {
		await updateStatus(ctx, "idle");
		if (ctx.hasUI) {
			ctx.ui.setStatus("agents-sidebar", undefined);
		}
	});
}
