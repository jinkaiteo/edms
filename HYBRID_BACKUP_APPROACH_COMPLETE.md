# Hybrid Backup/Restore Approach - Complete Documentation

**Date:** 2026-01-11  
**Status:** Recommended Solution  
**Complexity:** Low (100 lines vs 10,000)  
**Reliability:** High (Industry standard tools)  

---

## 📚 Table of Contents

1. [What Is The Hybrid Approach](#what-is-the-hybrid-approach)
2. [Why It's Called "Hybrid"](#why-its-called-hybrid)
3. [How It Works](#how-it-works)
4. [Component Breakdown](#component-breakdown)
5. [Backup Process Explained](#backup-process-explained)
6. [Restore Process Explained](#restore-process-explained)
7. [Complete Implementation](#complete-implementation)
8. [Scheduling & Automation](#scheduling--automation)
9. [Testing & Verification](#testing--verification)
10. [Disaster Recovery](#disaster-recovery)
11. [Advantages Over Current System](#advantages-over-current-system)
12. [Common Questions](#common-questions)

---

## What Is The Hybrid Approach?

The Hybrid Approach combines **two proven, industry-standard tools** instead of custom code:

1. **PostgreSQL's `pg_dump`** - For database backup
2. **rsync** - For media file backup

Both are then packaged into a single `.tar.gz` file for easy storage and transfer.

### Why "Hybrid"?

It's called "hybrid" because it combines:
- **Database tool** (pg_dump) + **File system tool** (rsync)
- **Binary backup** (database) + **File copy** (media)
- **PostgreSQL-specific** (database) + **Universal** (files)

---

## How It Works

### The Big Picture

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKUP PROCESS                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. pg_dump extracts database → database.dump               │
│     • All tables, data, constraints                         │
│     • Compressed format                                     │
│     • Atomic snapshot                                       │
│                                                              │
│  2. rsync copies media files → storage/                     │
│     • All uploaded documents                                │
│     • Preserves permissions                                 │
│     • Fast incremental copy                                 │
│                                                              │
│  3. Create manifest.json                                    │
│     • Timestamp                                             │
│     • Version info                                          │
│     • Backup metadata                                       │
│                                                              │
│  4. tar.gz everything → backup_YYYYMMDD_HHMMSS.tar.gz       │
│     • Single compressed file                                │
│     • Easy to store/transfer                                │
│     • Atomic unit                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   RESTORE PROCESS                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Extract tar.gz → /tmp/restore/                          │
│     • Unpack everything                                     │
│     • Verify contents                                       │
│                                                              │
│  2. pg_restore imports database                             │
│     • Recreates tables                                      │
│     • Loads all data                                        │
│     • Rebuilds indexes                                      │
│     • Enforces constraints                                  │
│                                                              │
│  3. rsync copies storage back → /app/storage/               │
│     • Restores all media files                              │
│     • Preserves permissions                                 │
│                                                              │
│  4. Cleanup temporary files                                 │
│     • Remove extracted files                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### Component 1: pg_dump (Database Backup)

**What it is:** PostgreSQL's official backup utility

**What it does:**
- Creates a complete snapshot of the database
- Exports all tables, data, sequences, indexes
- Maintains FK relationships and constraints
- Compresses data automatically
- Creates an atomic backup (consistent point-in-time)

**Why it's better than custom code:**
- Used by millions of PostgreSQL installations
- Optimized for speed and reliability
- Handles all edge cases (FKs, constraints, etc.)
- Maintained by PostgreSQL core team
- Zero custom code needed

**Example output:**
```
database.dump - 50MB compressed (200MB uncompressed)
Contains:
- 20 tables with full data
- All indexes and sequences
- All constraints and foreign keys
- Transaction-consistent snapshot
```

### Component 2: rsync (Media File Backup)

**What it is:** Unix utility for efficient file copying

**What it does:**
- Copies all files from source to destination
- Preserves file permissions and timestamps
- Fast incremental updates (only changed files)
- Reliable file transfer with checksums

**Why it's better than custom code:**
- Battle-tested since 1996
- Extremely fast and efficient
- Handles large files properly
- Preserves file metadata
- Zero custom code needed

**Example output:**
```
storage/ - 500MB
Contains:
- All uploaded documents (PDFs, DOCX, etc.)
- Version history files
- Generated PDFs
- User uploads
```

### Component 3: tar.gz (Packaging)

**What it is:** Standard Unix archiving and compression

**What it does:**
- Packages multiple files/folders into single archive
- Compresses the archive with gzip
- Creates portable, self-contained backup file
- Industry standard format

**Why it's useful:**
- Single file to manage (not 1000s of files)
- Easy to transfer/store
- Compressed (saves disk space)
- Universal format

**Example output:**
```
backup_20260111_120000.tar.gz - 400MB
Contains:
- database.dump (50MB compressed)
- storage/ (500MB → 350MB compressed)
- manifest.json (1KB)
```

### Component 4: manifest.json (Metadata)

**What it is:** Simple JSON file with backup information

**What it does:**
- Records backup timestamp
- Records git commit version
- Lists backup contents
- Helps identify/verify backups

**Example:**
```json
{
  "timestamp": "2026-01-11T12:00:00+08:00",
  "database": "database.dump",
  "storage": "storage/",
  "version": "6ace8e5a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e",
  "backup_type": "full",
  "database_size_mb": 50,
  "storage_size_mb": 500,
  "created_by": "automated_backup_script"
}
```

---

## Backup Process Explained

### Step-by-Step Walkthrough

#### Step 1: Create Backup Directory
```bash
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
```

**What happens:**
- Creates timestamped directory: `/backups/20260111_120000/`
- All backup files go here temporarily

---

#### Step 2: Database Backup
```bash
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --format=custom \
  --compress=9 \
  --file=$BACKUP_DIR/database.dump
```

**What happens:**
1. Connects to PostgreSQL database
2. Takes a consistent snapshot (no need to stop services!)
3. Exports all tables, data, indexes, constraints
4. Compresses with level 9 (maximum compression)
5. Saves to `database.dump`

**Technical details:**
- Format: PostgreSQL custom format (binary, optimized)
- Compression: GZIP level 9 (~70-80% reduction)
- Consistency: Transaction snapshot (atomic)
- Time: ~10-30 seconds for typical EDMS database
- Downtime: ZERO (services keep running)

**What's included:**
```
✅ All document records
✅ All user accounts
✅ All workflow data
✅ All audit trails
✅ All relationships (FKs)
✅ All sequences (auto-increment IDs)
✅ All indexes
✅ All constraints
```

---

#### Step 3: Media File Backup
```bash
rsync -av /app/storage/ $BACKUP_DIR/storage/
```

**What happens:**
1. Copies all files from `/app/storage/` to backup directory
2. Preserves file permissions, timestamps, ownership
3. Creates directory structure
4. Shows progress (-v = verbose)

**Options explained:**
- `-a` = Archive mode (recursive, preserve everything)
- `-v` = Verbose (show what's being copied)

**What's included:**
```
✅ All uploaded documents (PDF, DOCX, TXT, etc.)
✅ Version history files
✅ Generated PDFs
✅ Temporary files
✅ File structure and organization
```

**Time:** ~30-60 seconds for typical EDMS storage (1-5GB)

---

#### Step 4: Create Manifest
```bash
cat > $BACKUP_DIR/manifest.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "database": "database.dump",
  "storage": "storage/",
  "version": "$(git rev-parse HEAD)"
}
