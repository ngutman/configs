/**
 * Minimal footer for pi
 *
 * Replaces the built-in footer and removes the cwd/git-branch line.
 * Keeps one compact stats line + optional extension status line.
 */

import type { ExtensionAPI, ExtensionContext } from "@mariozechner/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@mariozechner/pi-tui";

function formatTokens(count: number): string {
	if (count < 1000) return count.toString();
	if (count < 10000) return `${(count / 1000).toFixed(1)}k`;
	if (count < 1000000) return `${Math.round(count / 1000)}k`;
	if (count < 10000000) return `${(count / 1000000).toFixed(1)}M`;
	return `${Math.round(count / 1000000)}M`;
}

function toNum(value: unknown): number {
	return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function sanitizeStatusText(text: string): string {
	return text.replace(/[\r\n\t]/g, " ").replace(/ +/g, " ").trim();
}

function applyMinimalFooter(ctx: ExtensionContext): void {
	if (!ctx.hasUI) return;

	ctx.ui.setFooter((_, theme, footerData) => ({
		invalidate() {},
		render(width: number): string[] {
			let totalInput = 0;
			let totalOutput = 0;
			let totalCacheRead = 0;
			let totalCacheWrite = 0;
			let totalCost = 0;

			for (const entry of ctx.sessionManager.getEntries()) {
				if (entry.type !== "message" || entry.message.role !== "assistant") continue;
				const usage = (entry.message as { usage?: unknown }).usage as
					| { input?: number; output?: number; cacheRead?: number; cacheWrite?: number; cost?: { total?: number } }
					| undefined;
				if (!usage) continue;
				totalInput += toNum(usage.input);
				totalOutput += toNum(usage.output);
				totalCacheRead += toNum(usage.cacheRead);
				totalCacheWrite += toNum(usage.cacheWrite);
				totalCost += toNum(usage.cost?.total);
			}

			const parts: string[] = [];
			if (totalInput) parts.push(theme.fg("dim", `↑${formatTokens(totalInput)}`));
			if (totalOutput) parts.push(theme.fg("dim", `↓${formatTokens(totalOutput)}`));
			if (totalCacheRead) parts.push(theme.fg("dim", `R${formatTokens(totalCacheRead)}`));
			if (totalCacheWrite) parts.push(theme.fg("dim", `W${formatTokens(totalCacheWrite)}`));

			const usingSubscription = ctx.model ? ctx.modelRegistry.isUsingOAuth(ctx.model) : false;
			if (totalCost || usingSubscription) {
				parts.push(theme.fg("dim", `$${totalCost.toFixed(3)}${usingSubscription ? " (sub)" : ""}`));
			}

			const usage = ctx.getContextUsage();
			const contextPercent = usage?.percent ?? 0;
			const contextWindow = usage?.contextWindow ?? ctx.model?.contextWindow ?? 0;
			const contextDisplay = `${contextPercent.toFixed(1)}%/${formatTokens(contextWindow)}`;
			if (contextPercent > 90) {
				parts.push(theme.fg("error", contextDisplay));
			} else if (contextPercent > 70) {
				parts.push(theme.fg("warning", contextDisplay));
			} else {
				parts.push(theme.fg("dim", contextDisplay));
			}

			const left = parts.join(" ");

			const modelName = ctx.model?.id || "no-model";
			let right = modelName;
			if (ctx.model && footerData.getAvailableProviderCount() > 1) {
				right = `(${ctx.model.provider}) ${modelName}`;
			}
			right = theme.fg("dim", right);

			const leftW = visibleWidth(left);
			const minPadding = 2;
			let line = left;

			if (leftW + minPadding < width) {
				const availableRight = Math.max(0, width - leftW - minPadding);
				const rightTruncated = truncateToWidth(right, availableRight, "");
				const pad = " ".repeat(Math.max(minPadding, width - leftW - visibleWidth(rightTruncated)));
				line = left + pad + rightTruncated;
			}

			const lines = [truncateToWidth(line, width, theme.fg("dim", "..."))];

			const extensionStatuses = footerData.getExtensionStatuses();
			if (extensionStatuses.size > 0) {
				const statusLine = Array.from(extensionStatuses.entries())
					.sort(([a], [b]) => a.localeCompare(b))
					.map(([, text]) => sanitizeStatusText(text))
					.join(" ");
				if (statusLine) {
					lines.push(truncateToWidth(statusLine, width, theme.fg("dim", "...")));
				}
			}

			return lines;
		},
	}));
}

export default function minimalFooterExtension(pi: ExtensionAPI) {
	pi.on("session_start", (_event, ctx) => {
		applyMinimalFooter(ctx);
	});

	pi.on("session_switch", (_event, ctx) => {
		applyMinimalFooter(ctx);
	});

	pi.on("session_fork", (_event, ctx) => {
		applyMinimalFooter(ctx);
	});

	pi.registerCommand("footer-minimal", {
		description: "re-apply minimal footer (no cwd/git line)",
		handler: async (_args, ctx) => {
			if (!ctx.hasUI) return;
			applyMinimalFooter(ctx);
			ctx.ui.notify("Minimal footer applied", "info");
		},
	});

	pi.registerCommand("footer-default", {
		description: "restore built-in footer",
		handler: async (_args, ctx) => {
			if (!ctx.hasUI) return;
			ctx.ui.setFooter(undefined);
			ctx.ui.notify("Default footer restored", "info");
		},
	});
}
