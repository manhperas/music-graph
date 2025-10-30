# Band Classification Documentation

## 📋 Overview

The `classify_bands.py` script analyzes Wikipedia data to classify artists as either **bands** or **solo artists**. This classification is essential for creating proper graph relationships in the music network.

## 🎯 Purpose

- **Distinguish bands from solo artists** for accurate graph modeling
- **Support future tasks**: Creating Band nodes and MEMBER_OF relationships
- **Improve data quality**: Better understanding of artist structure

## 🔍 Classification Methods

The classifier uses a **multi-factor scoring system** that analyzes:

### 1. Wikipedia Categories
- **Band indicators**: "nhóm nhạc", "ban nhạc", "musical groups", "bands"
- **Solo indicators**: "ca sĩ", "nghệ sĩ", "solo artist", "singer"
- **Score**: +1 for each matching keyword

### 2. Name Patterns
- **Band patterns**:
  - Names starting with "The" (e.g., "The Beatles", "The Chainsmokers")
  - Names containing "&" or "and" (e.g., "Simon & Garfunkel")
  - Multi-word names (more likely to be bands)
- **Solo patterns**:
  - First Last format (e.g., "Taylor Swift", "Ed Sheeran")
- **Score**: +1 to +2 per pattern match

### 3. Infobox Analysis
- **Members field**: Strong indicator of band (+3 score)
- **Background field**: 
  - `background = solo_singer` → Solo (+2)
  - `background = group` → Band (+3)

### 4. Text Content Analysis
- **Band keywords**: "nhóm nhạc", "ban nhạc", "members", "formed"
- **Solo keywords**: "ca sĩ", "nghệ sĩ", "singer", "songwriter"
- **Score**: +1 to +2 per keyword match (capped per pattern)

## 📊 Classification Logic

```python
total_band_score = category_score + name_score + infobox_score + text_score
total_solo_score = category_score + name_score + infobox_score + text_score

if total_band_score > total_solo_score:
    classification = 'band'
elif total_solo_score > total_band_score:
    classification = 'solo'
else:
    classification = 'unknown'
```

**Confidence Score**: Calculated as the ratio of the winning score to total score.

## 🚀 Usage

### Basic Usage

```bash
# Test with seed artists (recommended first step)
python scripts/classify_bands.py --test-seed --verbose

# Classify all artists
python scripts/classify_bands.py \
    --input data/processed/parsed_artists.json \
    --raw-input data/raw/artists.json \
    --output data/processed/band_classifications.json

# Test with sample of N artists
python scripts/classify_bands.py --test-sample 10 --verbose
```

### Command Line Options

- `--input, -i`: Input JSON file with parsed artist data (default: `data/processed/parsed_artists.json`)
- `--raw-input, -r`: Raw input JSON file with infobox and text (default: `data/raw/artists.json`)
- `--output, -o`: Output JSON file for classifications (default: `data/processed/band_classifications.json`)
- `--test-seed`: Test with seed artists only
- `--test-sample N`: Test with first N artists only
- `--verbose, -v`: Verbose output

## 📈 Output Format

The script generates a JSON file with classification results:

```json
[
  {
    "name": "Taylor Swift",
    "classification": "solo",
    "confidence": 0.875,
    "band_score": 2,
    "solo_score": 14,
    "categories": ["Ca sĩ Mỹ", "Nhạc sĩ Mỹ"],
    "indicators": [
      "Solo category: ca sĩ",
      "Solo name pattern: First Last",
      "Infobox indicates solo singer"
    ],
    "category_analysis": {...},
    "name_analysis": {...},
    "infobox_analysis": {...},
    "text_analysis": {...}
  }
]
```

## 📊 Statistics

The script generates summary statistics:

- Total artists classified
- Breakdown: bands, solo, unknown, errors
- Average confidence score
- Top examples for each category

Example output:
```
CLASSIFICATION STATISTICS
============================================================
Total artists: 20
Bands: 3 (15.0%)
Solo artists: 16 (80.0%)
Unknown: 1 (5.0%)
Average confidence: 0.82

Top band examples: The Chainsmokers, Maroon 5, One Direction
Top solo examples: Taylor Swift, Ed Sheeran, Adele
```

## 🧪 Testing

### Test with Seed Artists

The seed artists include known bands and solo artists:
- **Solo artists**: Taylor Swift, Ed Sheeran, Adele, Bruno Mars, etc.
- **Bands**: The Chainsmokers, Maroon 5

Run:
```bash
python scripts/classify_bands.py --test-seed --verbose
```

This will:
1. Load seed artists from `config/seed_artists.json`
2. Fetch Wikipedia categories for each
3. Analyze all indicators
4. Generate classification results
5. Display statistics

### Expected Results

Based on seed artists:
- **Solo artists** should be classified with high confidence (>0.7)
- **Bands** like "The Chainsmokers" and "Maroon 5" should be classified as bands
- Categories should be retrieved successfully

## 🔧 Refining Rules

If classification accuracy is low, refine rules by:

1. **Analyzing misclassifications**: Check indicators for false positives/negatives
2. **Adjusting scores**: Modify score weights in the classifier
3. **Adding patterns**: Add new name patterns or keywords
4. **Improving category matching**: Expand keyword lists

Example refinement:
```python
# In BandClassifier.__init__()
self.band_category_keywords.add('new_keyword')
self.band_name_patterns.append(r'new_pattern')
```

## 📝 Next Steps

After classification:

1. **Analyze results**: Review classification accuracy
2. **Refine rules**: Adjust patterns and scores if needed
3. **Create Band nodes**: Extract band memberships
4. **Create MEMBER_OF relationships**: Link artists to bands

## ⚠️ Limitations

- **Wikipedia API rate limits**: May need delays between requests
- **Category availability**: Some artists may not have relevant categories
- **Language-specific**: Currently optimized for Vietnamese Wikipedia
- **Ambiguous cases**: Some artists may be classified as "unknown"

## 🔗 Related Files

- `scripts/classify_bands.py`: Main classification script
- `config/seed_artists.json`: Seed artists for testing
- `data/raw/artists.json`: Raw Wikipedia data
- `data/processed/parsed_artists.json`: Parsed artist data
- `data/processed/band_classifications.json`: Classification results (output)

## ✅ Status

**Task 4.1: Band Classification Logic** - ✅ Completed

- [x] Analyze Wikipedia categories
- [x] Create classification rules
- [x] Test với seed artists
- [x] Refine rules (ready for refinement based on test results)

