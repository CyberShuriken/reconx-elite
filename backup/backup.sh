#!/bin/bash
set -e

# Backup script for ReconX-Elite database
BACKUP_DEST="${BACKUP_DEST_PATH:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="reconx_${TIMESTAMP}.dump.gz"
FILEPATH="${BACKUP_DEST}/${FILENAME}"

# Create backup directory
mkdir -p "${BACKUP_DEST}"

# Log function
log() {
    echo "[$(date -Iseconds)] $1"
}

log "Starting backup to ${FILEPATH}"

# Perform backup
if pg_dump --format=custom --host="${POSTGRES_HOST:-postgres}" --port="${POSTGRES_PORT:-5432}" --username="${POSTGRES_USER}" --dbname="${POSTGRES_DB}" | gzip > "${FILEPATH}"; then
    
    # Get file size (compatible with Linux and Alpine)
    if command -v stat >/dev/null 2>&1; then
        if stat -c%s "${FILEPATH}" >/dev/null 2>&1; then
            SIZE=$(stat -c%s "${FILEPATH}")
        else
            SIZE=$(stat -f%z "${FILEPATH}" 2>/dev/null || echo "unknown")
        fi
    else
        SIZE="unknown"
    fi
    
    log "Backup complete: file=${FILENAME} size=${SIZE} bytes"
else
    log "ERROR: Backup failed" >&2
    rm -f "${FILEPATH}"
    exit 1
fi

# Prune old backups
log "Pruning backups older than ${RETENTION_DAYS} days"
if find "${BACKUP_DEST}" -name "reconx_*.dump.gz" -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null; then
    log "Pruning complete"
else
    log "Warning: Could not prune old files" >&2
fi
