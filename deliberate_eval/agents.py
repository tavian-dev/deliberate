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
) -> Trajectory:
    """Run Claude Code in headless mode and capture trajectory.

    Uses `claude -p --output-format json` for structured output.
    """
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--max-turns", str(max_turns),
        "--no-session-persistence",
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
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        if result.returncode != 0 and not result.stdout.strip():
            return Trajectory(
                duration_ms=duration_ms,
                error=result.stderr[:1000],
            )

        data = json.loads(result.stdout)
        usage = data.get("usage", {})

        return Trajectory(
            input_tokens=usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0),
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
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        # Codex reports token count in output footer
        output = result.stdout
        token_count = 0
        for line in output.split("\n"):
            if line.startswith("tokens used"):
                # Next line or same line might have the count
                pass
            if line.strip().isdigit():
                token_count = int(line.strip())

        return Trajectory(
            output_tokens=token_count,  # Codex only reports total
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
