"""Agent adapters for headless execution."""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

from deliberate_eval import Trajectory, AgentType


def run_claude(
    prompt: str,
    workdir: Path,
    timeout: int = 300,
    max_turns: int = 50,
    env: Optional[dict] = None,
) -> Trajectory:
    """Run Claude Code in headless mode and capture trajectory.

    Uses `claude -p --output-format json` for structured output.
    """
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--max-turns", str(max_turns),
        "--no-session-persistence",
        "--dangerously-skip-permissions",
    ]

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            env=env,
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        if result.returncode != 0 and not result.stdout.strip():
            return Trajectory(
                duration_ms=duration_ms,
                error=result.stderr[:1000],
            )

        data = json.loads(result.stdout)
        usage = data.get("usage", {})

        # Claude API token breakdown:
        #   input_tokens: fresh (non-cached) input
        #   cache_read_input_tokens: replayed context (cheap, ~10x less)
        #   cache_creation_input_tokens: new context written to cache
        # We store fresh input separately from cache reads so metrics
        # reflect actual work, not context replay overhead.
        input_tok = (usage.get("input_tokens", 0)
                     + usage.get("cache_creation_input_tokens", 0))

        return Trajectory(
            input_tokens=input_tok,
            output_tokens=usage.get("output_tokens", 0),
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            duration_ms=data.get("duration_ms", duration_ms),
            num_turns=data.get("num_turns", 0),
            error="" if not data.get("is_error") else data.get("result", "unknown error"),
        )

    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - start) * 1000)
        return Trajectory(duration_ms=duration_ms, error="timeout")
    except (json.JSONDecodeError, KeyError) as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        return Trajectory(duration_ms=duration_ms, error=f"parse error: {e}")


def run_codex(
    prompt: str,
    workdir: Path,
    timeout: int = 300,
    env: Optional[dict] = None,
) -> Trajectory:
    """Run Codex CLI in headless mode and capture trajectory."""
    cmd = [
        "codex", "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        prompt,
    ]

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            env=env,
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        # Codex reports "tokens used\nNNNN" in its output footer
        output = result.stdout
        token_count = 0
        lines = output.strip().split("\n")
        for i, line in enumerate(lines):
            if line.strip() == "tokens used" and i + 1 < len(lines):
                next_line = lines[i + 1].strip().replace(",", "")
                if next_line.isdigit():
                    token_count = int(next_line)
                break

        return Trajectory(
            input_tokens=token_count,  # Codex reports total, not split
            duration_ms=duration_ms,
            error="" if result.returncode == 0 else result.stderr[:1000],
        )

    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - start) * 1000)
        return Trajectory(duration_ms=duration_ms, error="timeout")


AGENT_RUNNERS = {
    AgentType.CLAUDE: run_claude,
    AgentType.CODEX: run_codex,
}
