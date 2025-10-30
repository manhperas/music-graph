# Phase 4 Validation Guide

## Overview

This guide provides instructions for validating Phase 4: Awards + AWARD_NOMINATION Relationships implementation.

## Prerequisites

1. **Award Data Files**:
   - `data/processed/awards.csv` - Award nodes CSV
   - `data/processed/awards.json` - Awards data (artist -> list of awards)

2. **Neo4j Running**:
   ```bash
   docker-compose up -d
   ```

3. **Python Dependencies**:
   - All dependencies from `requirements.txt` installed

## Step-by-Step Validation

### Step 1: Extract Awards (if not already done)

```bash
# Extract awards from seed artists
python scripts/extract_awards.py \
    --seed-file config/seed_artists.json \
    --output-file data/processed/awards.json \
    --max-artists 50

# Create awards CSV
python scripts/extract_awards.py \
    --create-csv \
    --output-file data/processed/awards.json \
    --awards-csv data/processed/awards.csv
```

### Step 2: Build Graph with Awards

```bash
# Build graph including awards
python src/main.py build
```

### Step 3: Verify CSV Exports

Check that the following files exist and contain data:

```bash
# Check awards.csv
head -5 data/processed/awards.csv

# Check edges.csv for AWARD_NOMINATION
grep "AWARD_NOMINATION" data/processed/edges.csv | head -5
```

### Step 4: Import to Neo4j

```bash
# Import to Neo4j
python src/main.py import
```

### Step 5: Run Validation Script

```bash
# Run comprehensive validation
python scripts/validate_phase4.py
```

This script will validate all aspects of Phase 4 implementation.

### Step 6: Manual Cypher Queries

Run queries from `docs/implementation/PHASE_4_CYPHER_QUERIES.md` in Neo4j Browser.

## Expected Results

- ✅ Award nodes created in graph
- ✅ AWARD_NOMINATION edges created
- ✅ CSV exports successful
- ✅ Neo4j import successful
- ✅ ≥80% seed artists have awards

