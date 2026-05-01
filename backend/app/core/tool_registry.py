"""Tool Registry for ReconX Elite 10-Phase Pipeline.

Defines required and optional security tools per Master Prompt.
Maps tools to their respective pipeline phases.
"""

from dataclasses import dataclass
from typing import TypedDict


class ToolInfo(TypedDict):
    """Information about a security tool."""

    name: str
    description: str
    phases: list[str]
    install_hint: str
    required: bool


# Core tools required for basic functionality
# These are the most reliable and important tools
REQUIRED_TOOLS: list[ToolInfo] = [
    {
        "name": "subfinder",
        "description": "Subdomain enumeration via passive sources",
        "phases": ["phase_1"],
        "install_hint": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
        "required": True,
    },
    {
        "name": "httpx",
        "description": "Fast HTTP prober with tech detection",
        "phases": ["phase_2"],
        "install_hint": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "required": True,
    },
    {
        "name": "nmap",
        "description": "Network port scanner and service fingerprinting",
        "phases": ["phase_3"],
        "install_hint": "apt-get install nmap (Linux) or brew install nmap (macOS)",
        "required": True,
    },
    {
        "name": "nuclei",
        "description": "Vulnerability scanner with templates",
        "phases": ["phase_6"],
        "install_hint": "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
        "required": True,
    },
    {
        "name": "dnsx",
        "description": "DNS resolver and query tool",
        "phases": ["phase_2"],
        "install_hint": "go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
        "required": True,
    },
]

# Optional tools - enhance functionality but scan continues if missing
OPTIONAL_TOOLS: list[ToolInfo] = [
    {
        "name": "sublist3r",
        "description": "Subdomain enumeration via search engines",
        "phases": ["phase_1"],
        "install_hint": "pip install sublist3r",
        "required": False,
    },
    {
        "name": "findomain",
        "description": "Fast cross-platform subdomain enumerator",
        "phases": ["phase_1"],
        "install_hint": "Download from github.com/Findomain/Findomain/releases",
        "required": False,
    },
    {
        "name": "massdns",
        "description": "High-performance DNS stub resolver",
        "phases": ["phase_1"],
        "install_hint": "git clone https://github.com/blechschmidt/massdns && cd massdns && make",
        "required": False,
    },
    {
        "name": "gobuster",
        "description": "Directory/file and DNS busting tool",
        "phases": ["phase_1"],
        "install_hint": "go install github.com/OJ/gobuster/v3@latest",
        "required": False,
    },
    {
        "name": "httprobe",
        "description": "Probe for working HTTP/HTTPS servers",
        "phases": ["phase_2"],
        "install_hint": "go install github.com/tomnomnom/httprobe@latest",
        "required": False,
    },
    {
        "name": "masscan",
        "description": "Fast TCP port scanner",
        "phases": ["phase_3"],
        "install_hint": "apt-get install masscan (Linux)",
        "required": False,
    },
    {
        "name": "katana",
        "description": "Fast crawler for JS file discovery",
        "phases": ["phase_4"],
        "install_hint": "go install github.com/projectdiscovery/katana/cmd/katana@latest",
        "required": False,
    },
    {
        "name": "hakrawler",
        "description": "Web crawler for link discovery",
        "phases": ["phase_4"],
        "install_hint": "go install github.com/hakluke/hakrawler@latest",
        "required": False,
    },
    {
        "name": "trufflehog",
        "description": "Secret scanner for credentials/tokens",
        "phases": ["phase_4"],
        "install_hint": "pip install trufflehog",
        "required": False,
    },
    {
        "name": "linkfinder",
        "description": "Extract endpoints from JS files",
        "phases": ["phase_4"],
        "install_hint": "git clone https://github.com/GerbenJavado/LinkFinder.git",
        "required": False,
    },
    {
        "name": "gau",
        "description": "GetAllUrls - fetch known URLs from AlienVault's OTX",
        "phases": ["phase_5"],
        "install_hint": "go install github.com/lc/gau/v2/cmd/gau@latest",
        "required": False,
    },
    {
        "name": "waybackurls",
        "description": "Fetch URLs from Wayback Machine",
        "phases": ["phase_5"],
        "install_hint": "go install github.com/tomnomnom/waybackurls@latest",
        "required": False,
    },
    {
        "name": "paramspider",
        "description": "Parameter discovery from web archives",
        "phases": ["phase_5"],
        "install_hint": "pip install paramspider",
        "required": False,
    },
    {
        "name": "arjun",
        "description": "HTTP parameter discovery suite",
        "phases": ["phase_5"],
        "install_hint": "pip install arjun",
        "required": False,
    },
    {
        "name": "gf",
        "description": "grep on steroids for pattern matching",
        "phases": ["phase_5"],
        "install_hint": "go install github.com/tomnomnom/gf@latest && git clone https://github.com/1ndianl33t/Gf-Patterns ~/.gf",
        "required": False,
    },
    {
        "name": "subjack",
        "description": "Subdomain takeover detection",
        "phases": ["phase_6"],
        "install_hint": "go install github.com/haccer/subjack@latest",
        "required": False,
    },
    {
        "name": "kxss",
        "description": "XSS reflection tester",
        "phases": ["phase_6"],
        "install_hint": "go install github.com/Emoe/kxss@latest",
        "required": False,
    },
    {
        "name": "dalfox",
        "description": "Modern XSS scanner",
        "phases": ["phase_6"],
        "install_hint": "go install github.com/hahwul/dalfox/v2@latest",
        "required": False,
    },
    {
        "name": "sqlmap",
        "description": "Automatic SQL injection tool",
        "phases": ["phase_6"],
        "install_hint": "pip install sqlmap",
        "required": False,
    },
    {
        "name": "ghauri",
        "description": "Advanced SQL injection tool",
        "phases": ["phase_6"],
        "install_hint": "pip install ghauri",
        "required": False,
    },
    {
        "name": "interactsh-client",
        "description": "OOB interaction client for SSRF/blind XSS",
        "phases": ["phase_6"],
        "install_hint": "go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest",
        "required": False,
    },
    {
        "name": "cloud_enum",
        "description": "Cloud storage bucket enumeration",
        "phases": ["phase_6"],
        "install_hint": "git clone https://github.com/initstring/cloud_enum.git && pip install -r requirements.txt",
        "required": False,
    },
    {
        "name": "curl",
        "description": "Command line HTTP client",
        "phases": ["phase_2", "phase_6"],
        "install_hint": "apt-get install curl (Linux) or brew install curl (macOS)",
        "required": False,
    },
    {
        "name": "wget",
        "description": "Network downloader for JS files",
        "phases": ["phase_4"],
        "install_hint": "apt-get install wget (Linux) or brew install wget (macOS)",
        "required": False,
    },
]

# All tools combined
ALL_TOOLS: list[ToolInfo] = REQUIRED_TOOLS + OPTIONAL_TOOLS

# Tool-to-phase mapping for quick lookup
TOOLS_BY_PHASE: dict[str, list[str]] = {
    "phase_0": [],  # Orchestrator doesn't need tools
    "phase_1": ["subfinder", "sublist3r", "findomain", "massdns", "gobuster"],
    "phase_2": ["dnsx", "httpx", "httprobe", "curl"],
    "phase_3": ["nmap", "masscan"],
    "phase_4": ["katana", "hakrawler", "trufflehog", "linkfinder", "wget"],
    "phase_5": ["gau", "waybackurls", "paramspider", "arjun", "gf"],
    "phase_6": [
        "subjack",
        "nuclei",
        "kxss",
        "dalfox",
        "sqlmap",
        "ghauri",
        "interactsh-client",
        "cloud_enum",
        "curl",
    ],
    "phase_7": [],  # AI analysis only
    "phase_8": [],  # AI analysis only
    "phase_9": [],  # AI correlation only
    "phase_10": [],  # Report generation only
}


def get_tool_info(tool_name: str) -> ToolInfo | None:
    """Get information about a specific tool.

    Args:
        tool_name: The tool name to look up

    Returns:
        ToolInfo dict or None if not found
    """
    for tool in ALL_TOOLS:
        if tool["name"] == tool_name:
            return tool
    return None


def get_tools_for_phase(phase: str) -> list[ToolInfo]:
    """Get all tools used in a specific phase.

    Args:
        phase: Phase name (e.g., 'phase_1')

    Returns:
        List of ToolInfo dicts for that phase
    """
    tool_names = TOOLS_BY_PHASE.get(phase, [])
    return [get_tool_info(name) for name in tool_names if get_tool_info(name)]


def get_required_tools() -> list[ToolInfo]:
    """Get list of required tools."""
    return REQUIRED_TOOLS


def get_optional_tools() -> list[ToolInfo]:
    """Get list of optional tools."""
    return OPTIONAL_TOOLS


def get_all_tools() -> list[ToolInfo]:
    """Get list of all tools (required + optional)."""
    return ALL_TOOLS


def is_tool_required(tool_name: str) -> bool:
    """Check if a tool is required.

    Args:
        tool_name: The tool name to check

    Returns:
        True if required, False otherwise
    """
    tool = get_tool_info(tool_name)
    return tool["required"] if tool else False


def get_install_hint(tool_name: str) -> str:
    """Get installation hint for a tool.

    Args:
        tool_name: The tool name

    Returns:
        Installation command/instructions
    """
    tool = get_tool_info(tool_name)
    return tool["install_hint"] if tool else "Tool not found in registry"


@dataclass
class ToolAvailabilityReport:
    """Report of tool availability status."""

    available: list[str]
    missing_required: list[str]
    missing_optional: list[str]
    total: int
    available_count: int
    missing_count: int

    def is_phase_executable(self, phase: str) -> bool:
        """Check if a phase can be executed with available tools.

        Args:
            phase: Phase name to check

        Returns:
            True if phase can be executed (all required tools available)
        """
        phase_tools = get_tools_for_phase(phase)
        required_in_phase = [t for t in phase_tools if t["required"]]

        for tool in required_in_phase:
            if tool["name"] not in self.available:
                return False

        return True

    def get_missing_tools_for_phase(self, phase: str) -> list[str]:
        """Get list of missing tools for a specific phase.

        Args:
            phase: Phase name

        Returns:
            List of missing tool names
        """
        phase_tools = get_tools_for_phase(phase)
        tool_names = [t["name"] for t in phase_tools]
        return [name for name in tool_names if name not in self.available]
