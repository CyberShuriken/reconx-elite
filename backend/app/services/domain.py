import re

DOMAIN_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$")


def normalize_domain(value: str) -> str:
    forbidden = (" ", "/", "\\", ":", "@", "?", "&", ";", "|", "$", "`", "'", "\"", "(", ")")
    if any(ch in value for ch in forbidden):
        raise ValueError("Invalid domain format")
    domain = value.strip().lower().rstrip(".")
    if domain.startswith("http://") or domain.startswith("https://"):
        raise ValueError("Provide domain only, without scheme")
    if len(domain) > 253:
        raise ValueError("Domain too long")
    if not DOMAIN_RE.fullmatch(domain):
        raise ValueError("Invalid domain format")
    return domain
