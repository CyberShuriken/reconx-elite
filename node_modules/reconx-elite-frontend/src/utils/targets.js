const DOMAIN_RE = /^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$/;

export function normalizeDomainInput(value) {
  const raw = value.trim();
  if (!raw) {
    throw new Error("Domain is required");
  }

  let host = raw;
  try {
    if (raw.includes("://") || raw.startsWith("//")) {
      host = new URL(raw.includes("://") ? raw : `http:${raw}`).hostname;
    } else {
      host = raw.split("/")[0].split("?")[0].split("#")[0];
    }
  } catch {
    throw new Error("Invalid domain format");
  }

  const domain = host.trim().toLowerCase().replace(/\.$/, "");
  if (!DOMAIN_RE.test(domain)) {
    throw new Error("Invalid domain format");
  }
  return domain;
}
