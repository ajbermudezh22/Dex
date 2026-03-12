#!/usr/bin/env python3
"""
Integration Detection Helper

Detects existing MCP configurations for Notion, Slack, Google, and Linear.
Used by onboarding and /dex-update to offer smart upgrade paths.

Linear uses a different detection approach: it relies on Claude Code's built-in
OAuth (mcp__linear__* tools) rather than npx packages in Claude Desktop config.
"""

import json
import os
from pathlib import Path
from typing import Optional, TypedDict


class IntegrationStatus(TypedDict):
    installed: bool
    package: Optional[str]
    version: Optional[str]
    config_path: Optional[str]
    is_dex_recommended: bool
    recommendation: Optional[str]

class DetectionResult(TypedDict):
    notion: IntegrationStatus
    slack: IntegrationStatus
    google: IntegrationStatus
    linear: IntegrationStatus
    any_installed: bool
    any_upgradeable: bool

# Dex recommended packages
RECOMMENDED = {
    "notion": {
        "package": "@notionhq/notion-mcp-server",
        "name": "Official Notion MCP",
        "benefits": ["Official from Notion", "Best maintained", "Full API coverage"]
    },
    "slack": {
        "package": "slack-mcp-server",
        "name": "Slack MCP Server",
        "benefits": ["No bot required", "Cookie auth supported", "Full history access"]
    },
    "google": {
        "package": "mcp-google",
        "name": "Google Workspace MCP",
        "benefits": ["Calendar + Gmail + Contacts", "OAuth helper", "Well documented"]
    },
    "linear": {
        "package": "mcp__linear (built-in OAuth)",
        "name": "Linear (Claude Code OAuth)",
        "benefits": ["No API key needed", "Built-in OAuth via /mcp", "Full issue/project/cycle access"]
    }
}

# Known alternative packages (for detection)
KNOWN_PACKAGES = {
    "notion": [
        "@notionhq/notion-mcp-server",  # Official (recommended)
        "@suekou/mcp-notion-server",
        "notion-mcp-server",
        "mcp-notion",
    ],
    "slack": [
        "slack-mcp-server",  # Recommended
        "@kazuph/mcp-slack",
        "shouting-mcp-slack",
        "mcp-slack",
    ],
    "google": [
        "mcp-google",  # Recommended
        "mcp-google-calendar",
        "mcp-google-drive",
        "mcp-google-docs",
        "@suncreation/mcp-google-docs",
        "mcp-google-sheets",
    ],
    "linear": [
        "mcp__linear",        # Built-in OAuth (recommended — no package needed)
        "linear-mcp-server",
        "mcp-linear",
        "@anthropic/linear-mcp",
    ]
}


def get_claude_config_path() -> Optional[Path]:
    """Find Claude Desktop config file."""
    # macOS
    mac_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if mac_path.exists():
        return mac_path
    
    # Windows
    win_path = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    if win_path.exists():
        return win_path
    
    # Linux
    linux_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    if linux_path.exists():
        return linux_path
    
    return None


def load_claude_config() -> Optional[dict]:
    """Load Claude Desktop MCP configuration."""
    config_path = get_claude_config_path()
    if not config_path:
        return None
    
    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def detect_builtin_oauth(service: str, available_tools: Optional[list] = None) -> IntegrationStatus:
    """Detect if a built-in OAuth integration is connected.

    Built-in OAuth integrations (like Linear) use Claude Code's /mcp command
    and appear as mcp__<service>__* tools rather than npx packages.

    Args:
        service: Integration name (e.g., "linear")
        available_tools: List of available tool names. If None, returns unknown status.
    """
    result: IntegrationStatus = {
        "installed": False,
        "package": None,
        "version": None,
        "config_path": "Claude Code built-in OAuth",
        "is_dex_recommended": True,  # Built-in OAuth is always the recommended approach
        "recommendation": None
    }

    if available_tools is None:
        return result

    prefix = f"mcp__{service}__"
    matching = [t for t in available_tools if t.startswith(prefix)]

    if matching:
        result["installed"] = True
        result["package"] = f"mcp__{service} (built-in OAuth)"

    return result


# Services that use built-in OAuth instead of npx packages
BUILTIN_OAUTH_SERVICES = {"linear"}


def detect_integration(service: str, config: dict, available_tools: Optional[list] = None) -> IntegrationStatus:
    """Detect if a specific integration is installed.

    For built-in OAuth services (Linear), checks available tools instead of config.
    For npx-based services (Notion, Slack, Google), checks Claude Desktop config.
    """
    # Built-in OAuth services use a different detection path
    if service in BUILTIN_OAUTH_SERVICES:
        return detect_builtin_oauth(service, available_tools)

    result: IntegrationStatus = {
        "installed": False,
        "package": None,
        "version": None,
        "config_path": str(get_claude_config_path()),
        "is_dex_recommended": False,
        "recommendation": None
    }

    mcp_servers = config.get("mcpServers", {})
    known = KNOWN_PACKAGES.get(service, [])
    recommended = RECOMMENDED.get(service, {}).get("package")

    # Check each known package
    for server_name, server_config in mcp_servers.items():
        # Check by command/args for npx-style configs
        command = server_config.get("command", "")
        args = server_config.get("args", [])

        # Detect package from npx command
        if command == "npx":
            for arg in args:
                if any(pkg in arg for pkg in known):
                    result["installed"] = True
                    result["package"] = arg.split("@")[0] if "@" in arg else arg
                    result["is_dex_recommended"] = arg.startswith(recommended) if recommended else False
                    break

        # Also check server name for matches
        server_lower = server_name.lower()
        if any(svc in server_lower for svc in [service, service.replace("google", "goog")]):
            result["installed"] = True
            if not result["package"]:
                result["package"] = server_name

    # Add recommendation if not using Dex recommended
    if result["installed"] and not result["is_dex_recommended"] and recommended:
        rec = RECOMMENDED[service]
        result["recommendation"] = f"Dex recommends {rec['name']} ({rec['package']}): {', '.join(rec['benefits'])}"

    return result


def detect_all_integrations(available_tools: Optional[list] = None) -> DetectionResult:
    """Detect all productivity integrations.

    Args:
        available_tools: List of available tool names for detecting built-in OAuth
                        integrations (e.g., Linear). Pass tool names from the current
                        session if available.
    """
    config = load_claude_config() or {}

    result: DetectionResult = {
        "notion": detect_integration("notion", config),
        "slack": detect_integration("slack", config),
        "google": detect_integration("google", config),
        "linear": detect_integration("linear", config, available_tools),
        "any_installed": False,
        "any_upgradeable": False
    }

    services = ["notion", "slack", "google", "linear"]

    result["any_installed"] = any(
        result[svc]["installed"] for svc in services
    )

    result["any_upgradeable"] = any(
        result[svc]["installed"] and not result[svc]["is_dex_recommended"]
        for svc in services
    )

    return result


def format_detection_report(result: DetectionResult) -> str:
    """Format detection results for user display."""
    lines = ["## Productivity Integration Status\n"]
    
    for service, status in [("Notion", result["notion"]),
                            ("Slack", result["slack"]),
                            ("Google", result["google"]),
                            ("Linear", result["linear"])]:
        if status["installed"]:
            emoji = "✅" if status["is_dex_recommended"] else "⚠️"
            lines.append(f"### {emoji} {service}")
            lines.append(f"- **Installed:** {status['package']}")
            if status["is_dex_recommended"]:
                lines.append("- **Status:** Using Dex recommended package")
            else:
                lines.append(f"- **Recommendation:** {status['recommendation']}")
        else:
            lines.append(f"### ❌ {service}")
            rec = RECOMMENDED.get(service.lower(), {})
            lines.append("- **Not installed**")
            lines.append(f"- **Recommended:** {rec.get('package', 'N/A')}")
            lines.append(f"- **Benefits:** {', '.join(rec.get('benefits', []))}")
        
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    result = detect_all_integrations()
    print(format_detection_report(result))
