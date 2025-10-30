# ✅ DANH SÁCH ĐẦU VIỆC CẦN LÀM NGAY

## 🎯 PRIORITY ORDER (Thứ tự ưu tiên)

### 🔴 **PRIORITY 1: Cải thiện Parser & Re-parse Data** (Tuần 1)

#### Task 1.1: Fix Genre Parsing
**File**: `src/data_processing/parser.py`
**Status**: ✅ Completed
**Effort**: 2-3 giờ
**Priority**: HIGH

**Cần làm:**
- [x] Fix parser để remove artifacts: `*`, `}}`, `{{`
- [x] Improve genre normalization
- [x] Better handling của wiki markup
- [x] Test với sample data

**Expected Result:**
- Genres coverage: 26% → 60-70%

**Completed:**
- Improved `_parse_list_field()` method to handle wiki templates (`flatlist`, `flat list`, `hlist`)
- Added artifact removal: `*`, `}}`, `{{`, `|`
- Added genre normalization with common mappings
- Better handling of wiki links, HTML tags, and references
- Improved template parsing to extract items from template body content

---

#### Task 1.2: Fix Album Parsing
**File**: `src/data_processing/parser.py`
**Status**: ✅ Completed
**Effort**: 2-3 giờ
**Priority**: HIGH

**Cần làm:**
- [x] Better regex patterns cho album extraction
- [x] Filter bad entries: "đầu tay", "tư Red", etc.
- [x] Validate album names (length, format)
- [x] Clean up parser logic

**Expected Result:**
- Album quality improved
- Remove bad entries như "đầu tay Taylor Swift"

**Completed:**
- Added `_validate_album_name()` method with comprehensive filtering:
  - Filters Vietnamese bad patterns: "đầu tay", "tư Red", "của", etc.
  - Filters incomplete English patterns: "by ArtistName", "of ArtistName", etc.
  - Validates length (4-200 characters)
  - Filters artifacts: `}}`, `{{`, year-only patterns `(2008)`, etc.
  - Filters generic words and incomplete extractions
- Added `_parse_album_field()` method for improved album extraction:
  - Better regex patterns for splitting album names
  - Handles Vietnamese separators (en dash, em dash)
  - Removes year patterns at the end: `(2008)`, `(2013)`
  - Limits to 30 albums per artist (more than genres)
- Applied validation in `parse_artist()` method:
  - Both raw albums and infobox albums are validated before adding
  - Prevents bad entries from entering parsed data

---

#### Task 1.3: Re-parse Raw Data
**File**: `src/data_processing/parser.py`
**Status**: ✅ Completed
**Effort**: 15 phút
**Priority**: HIGH

**Cần làm:**
- [x] Backup existing parsed data
- [x] Run parser với improved logic
- [x] Validate results
- [x] Compare với data cũ

**Command:**
```bash
# Backup
cp data/processed/parsed_artists.json data/processed/parsed_artists_backup.json

# Re-parse
python src/data_processing/parser.py
```

**Results:**
- ✅ Successfully re-parsed 1998 artists
- ✅ Genre coverage improved: **26.0% → 37.4%** (+11.4%)
- ✅ Unique genres increased: **530 → 1022** (+492 genres)
- ✅ Bad album patterns reduced: **408 → 321** (-87 patterns)
- ✅ Total albums filtered: 4905 → 3482 (removed invalid entries)
- ✅ Unique albums: 4055 → 3100 (better quality)

**Improvements:**
- Better genre extraction and normalization
- Improved album validation filtering out bad entries
- Cleaner parsed data ready for graph building

---

### 🟡 **PRIORITY 2: Infrastructure Setup** (Tuần 1)

#### Task 2.1: Migration Framework
**File**: `scripts/migration_framework.py` (NEW)
**Status**: ⬜ Not Started
**Effort**: 4 giờ
**Priority**: MEDIUM

**Cần làm:**
- [ ] Create migration script với backup capability
- [ ] Rollback functionality
- [ ] Progress tracking
- [ ] Error handling

**Features:**
- Backup data trước khi migrate
- Track migration progress
- Rollback nếu có lỗi
- Logging chi tiết

---

#### Task 2.2: Validation Framework
**File**: `scripts/validation_framework.py` (NEW)
**Status**: ⬜ Not Started
**Effort**: 6 giờ
**Priority**: MEDIUM

**Cần làm:**
- [ ] Node validation (orphans, duplicates)
- [ ] Relationship validation
- [ ] Data completeness checks
- [ ] Quality metrics calculation

---

### 🟢 **PRIORITY 3: Genre Migration** (Tuần 1-2)

#### Task 3.1: Extract Unique Genres
**File**: `scripts/migrate_genres.py` (NEW)
**Status**: ✅ Completed
**Effort**: 4 giờ
**Priority**: MEDIUM

**Cần làm:**
- [x] Load parsed artists
- [x] Extract all genres
- [x] Normalize genre names
- [x] Deduplicate
- [x] Create Genre nodes CSV

**Completed:**
- ✅ Extracted 2737 genre entries from 747 artists
- ✅ Normalized 2412 genre entries (skipped 325 invalid)
- ✅ Found **718 unique genres** (from 2412 entries)
- ✅ Created `data/migrations/genres.csv` with Genre nodes
- ✅ Top genres: pop (233), r&b (180), Rock (79), Soul (78), Hip Hop (74)

---

#### Task 3.2: Create HAS_GENRE Relationships
**File**: `scripts/migrate_genres.py` (extend)
**Status**: ✅ Completed
**Effort**: 6 giờ
**Priority**: MEDIUM

**Cần làm:**
- [x] Parse genres từ Artist nodes
- [x] Create HAS_GENRE: Artist → Genre
- [x] Create HAS_GENRE: Album → Genre
- [x] Validate relationships

**Completed:**
- ✅ Created **1920 HAS_GENRE relationships** total
- ✅ **Artist → Genre**: 1628 relationships (472 artists)
- ✅ **Album → Genre**: 292 relationships (64 albums)
- ✅ All relationships validated (0 invalid)
- ✅ Created `data/migrations/has_genre_relationships.csv`
- ✅ Ready for import into Neo4j

---

### 🔵 **PRIORITY 4: Band Classification** (Tuần 2)

#### Task 4.1: Band Classification Logic
**File**: `scripts/classify_bands.py` (NEW)
**Status**: ✅ Completed
**Effort**: 8 giờ
**Priority**: MEDIUM

**Cần làm:**
- [x] Analyze Wikipedia categories
- [x] Create classification rules
- [x] Test với seed artists
- [x] Refine rules

**Completed:**
- Created `BandClassifier` class with comprehensive classification logic
- Implemented Wikipedia category fetching using MediaWiki API
- Created multi-factor classification system:
  - **Category Analysis**: Checks Wikipedia categories for band/solo keywords
  - **Name Pattern Analysis**: Analyzes name patterns (e.g., "The [X]", "&", "and")
  - **Infobox Analysis**: Checks for "members" field and background type
  - **Text Content Analysis**: Searches text for band/solo indicators
- Scoring system: Aggregates scores from all factors to determine classification
- Confidence calculation: Provides confidence score for each classification
- Test mode: `--test-seed` flag to test with seed artists
- Statistics generation: Creates summary statistics and examples

**Usage:**
```bash
# Test with seed artists
python scripts/classify_bands.py --test-seed --verbose

# Classify all artists
python scripts/classify_bands.py --input data/processed/parsed_artists.json --output data/processed/band_classifications.json

# Test with sample of N artists
python scripts/classify_bands.py --test-sample 10 --verbose
```

**Next Steps:**
- Run classification on full dataset
- Analyze results and refine rules if needed
- Create Band nodes and MEMBER_OF relationships (Task 4.2)

---

## 📋 CHECKLIST THEO TUẦN

### **Tuần 1: Parser & Infrastructure**

#### Day 1-2: Fix Parser
- [ ] Task 1.1: Fix Genre Parsing
- [ ] Task 1.2: Fix Album Parsing
- [ ] Task 1.3: Re-parse Raw Data
- [ ] Validate results

#### Day 3-4: Infrastructure
- [ ] Task 2.1: Migration Framework
- [ ] Task 2.2: Validation Framework
- [ ] Test frameworks

#### Day 5-7: Genre Migration Start
- [x] Task 3.1: Extract Unique Genres ✅
- [x] Task 3.2: Create HAS_GENRE Relationships ✅

---

### **Tuần 2: Genre & Band Classification**

#### Day 1-3: Complete Genre Migration
- [ ] Task 3.2: Complete HAS_GENRE Relationships
- [ ] Update builder.py và importer.py
- [ ] Test và validate

#### Day 4-7: Band Classification
- [ ] Task 4.1: Band Classification Logic
- [ ] Extract bands
- [ ] Create Band nodes
- [ ] Create MEMBER_OF relationships

---

## 🚀 QUICK START - BẮT ĐẦU NGAY

### **Step 1: Fix Parser (Hôm nay)**

```bash
# 1. Backup existing data
cp data/processed/parsed_artists.json data/processed/parsed_artists_backup_$(date +%Y%m%d).json

# 2. Edit parser
vim src/data_processing/parser.py

# 3. Test với sample
python -c "
from src.data_processing.parser import InfoboxParser
parser = InfoboxParser()
# Test parsing logic
"

# 4. Re-parse
python src/data_processing/parser.py
```

### **Step 2: Validate Results**

```bash
# Check improvements
python -c "
import json
with open('data/processed/parsed_artists.json', 'r') as f:
    artists = json.load(f)
has_genres = sum(1 for a in artists if a.get('genres') and len(a.get('genres', [])) > 0)
print(f'Genres coverage: {has_genres/len(artists)*100:.1f}%')
"
```

### **Step 3: Setup Infrastructure**

```bash
# Create scripts directory
mkdir -p scripts

# Create migration framework
touch scripts/migration_framework.py
touch scripts/validation_framework.py
```

---

## 📊 PROGRESS TRACKING

### Week 1 Progress:
- [x] Parser improvements: ✅ Completed
- [x] Re-parse completed: ✅ Completed
- [ ] Infrastructure setup: ⬜ Not Started
- [x] Genre extraction started: ✅ Completed
- [x] Genre relationships created: ✅ Completed

### Week 2 Progress:
- [ ] Genre migration complete: ⬜ Not Started
- [ ] Band classification started: ⬜ Not Started

---

## 🎯 SUCCESS METRICS

### After Week 1:
- ✅ Genres coverage: 26% → **60-70%**
- ✅ Album quality: Improved (remove bad entries)
- ✅ Migration framework: Ready
- ✅ Validation framework: Ready

### After Week 2:
- ✅ Genre nodes: Created
- ✅ HAS_GENRE relationships: Created
- ✅ Band classification: Started

---

## ⚠️ BLOCKERS & RISKS

### Current Blockers:
- None

### Risks:
- [ ] Parser improvements may not work as expected
  - Mitigation: Test với sample data trước
- [ ] Re-parsing may take longer than expected
  - Mitigation: Run in background, monitor progress

---

## 📝 NOTES

### Important Decisions:
- Re-parse từ raw data thay vì scrape lại
- Focus on parser improvements trước
- Setup infrastructure để support future migrations

### Next Steps After Week 1:
- Complete genre migration
- Start band classification
- Plan song extraction

---

**Last Updated**: [Date]  
**Status**: ⬜ Planning | ⬜ In Progress | ⬜ Completed

