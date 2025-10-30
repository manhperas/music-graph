#!/bin/bash
# Helper script for band classification

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

LOG_FILE="/tmp/classification_full.log"
OUTPUT_FILE="data/processed/band_classifications_full.json"

case "$1" in
    start|run)
        echo "🚀 Starting band classification..."
        echo "   Output: $OUTPUT_FILE"
        echo "   Log: $LOG_FILE"
        echo "   Estimated time: ~15-20 minutes"
        echo ""
        
        PYTHONUNBUFFERED=1 uv run python -u scripts/classify_bands.py \
            --input data/processed/parsed_artists.json \
            --raw-input data/raw/artists.json \
            --output "$OUTPUT_FILE" \
            --verbose 2>&1 | tee "$LOG_FILE"
        ;;
    
    background|bg)
        echo "🚀 Starting band classification in background..."
        echo "   Output: $OUTPUT_FILE"
        echo "   Log: $LOG_FILE"
        echo ""
        
        nohup env PYTHONUNBUFFERED=1 uv run python -u scripts/classify_bands.py \
            --input data/processed/parsed_artists.json \
            --raw-input data/raw/artists.json \
            --output "$OUTPUT_FILE" \
            --verbose > "$LOG_FILE" 2>&1 &
        
        PID=$!
        echo "✅ Process started with PID: $PID"
        echo "   Monitor with: ./scripts/run_classification.sh log"
        echo "   Check progress: ./scripts/run_classification.sh progress"
        echo "   Stop: ./scripts/run_classification.sh stop"
        ;;
    
    log|tail)
        if [ -f "$LOG_FILE" ]; then
            echo "📋 Showing log (Ctrl+C to exit):"
            tail -f "$LOG_FILE"
        else
            echo "❌ Log file not found: $LOG_FILE"
            echo "   Run with: ./scripts/run_classification.sh start"
        fi
        ;;
    
    progress|status)
        echo "📊 Classification Progress:"
        echo ""
        
        if [ -f "$OUTPUT_FILE" ]; then
            python3 << EOF
import json, os
f = "$OUTPUT_FILE"
data = json.load(open(f))
total = len(data)
bands = sum(1 for x in data if x.get('classification') == 'band')
solo = sum(1 for x in data if x.get('classification') == 'solo')
unknown = sum(1 for x in data if x.get('classification') == 'unknown')
size = os.path.getsize(f) / 1024

print(f"✅ Progress: {total}/1998 ({total*100/1998:.1f}%)")
print(f"   Bands: {bands}")
print(f"   Solo: {solo}")
print(f"   Unknown: {unknown}")
print(f"   File size: {size:.1f} KB")
if total < 1998:
    remaining = (1998 - total) * 0.5 / 60
    print(f"   Estimated remaining: ~{remaining:.1f} minutes")
else:
    print(f"   ✅ COMPLETED!")
    
    # Show confidence
    if data:
        avg_conf = sum(x.get('confidence', 0) for x in data if x.get('confidence')) / len(data)
        print(f"   Average confidence: {avg_conf:.2f}")
EOF
        else
            if [ -f "$LOG_FILE" ]; then
                count=$(grep -c "\[.*/1998\] Classifying" "$LOG_FILE" 2>/dev/null || echo "0")
                echo "⏳ File chưa được tạo."
                echo "   Artists processed (from log): $count/1998"
                echo "   Check log: ./scripts/run_classification.sh log"
            else
                echo "⏳ No progress yet. Start with: ./scripts/run_classification.sh start"
            fi
        fi
        ;;
    
    stats|statistics)
        if [ -f "$OUTPUT_FILE" ]; then
            python3 << EOF
import json

f = "$OUTPUT_FILE"
with open(f, 'r') as file:
    data = json.load(file)

bands = [x for x in data if x.get('classification') == 'band']
solos = [x for x in data if x.get('classification') == 'solo']
unknown = [x for x in data if x.get('classification') == 'unknown']

print("=" * 60)
print("CLASSIFICATION STATISTICS")
print("=" * 60)
print(f"Total artists: {len(data)}")
print(f"Bands: {len(bands)} ({len(bands)/len(data)*100:.1f}%)")
print(f"Solo artists: {len(solos)} ({len(solos)/len(data)*100:.1f}%)")
print(f"Unknown: {len(unknown)} ({len(unknown)/len(data)*100:.1f}%)")

if data:
    avg_conf = sum(x.get('confidence', 0) for x in data if x.get('confidence')) / len(data)
    print(f"Average confidence: {avg_conf:.2f}")

if bands:
    print("\nTop 10 Bands:")
    for i, band in enumerate(sorted(bands, key=lambda x: x.get('confidence', 0), reverse=True)[:10], 1):
        print(f"  {i}. {band['name']} (confidence: {band.get('confidence', 0):.2f})")

if solos:
    print("\nTop 10 Solo Artists:")
    for i, solo in enumerate(sorted(solos, key=lambda x: x.get('confidence', 0), reverse=True)[:10], 1):
        print(f"  {i}. {solo['name']} (confidence: {solo.get('confidence', 0):.2f})")
EOF
        else
            echo "❌ Output file not found: $OUTPUT_FILE"
            echo "   Run classification first: ./scripts/run_classification.sh start"
        fi
        ;;
    
    stop|kill)
        echo "🛑 Stopping classification process..."
        pkill -f "classify_bands.py" && echo "✅ Process stopped" || echo "❌ No process found"
        ;;
    
    test)
        echo "🧪 Testing with sample (10 artists)..."
        uv run python scripts/classify_bands.py \
            --test-sample 10 \
            --verbose 2>&1 | tee /tmp/classification_test.log
        ;;
    
    test-seed)
        echo "🧪 Testing with seed artists..."
        uv run python scripts/classify_bands.py \
            --test-seed \
            --verbose 2>&1 | tee /tmp/classification_seed.log
        ;;
    
    monitor|watch)
        echo "👀 Monitoring classification progress..."
        echo "   Press Ctrl+C to exit"
        echo ""
        
        while true; do
            clear
            echo "=========================================="
            echo "BAND CLASSIFICATION MONITOR"
            echo "=========================================="
            echo ""
            
            # Check if process is running
            if pgrep -f "classify_bands.py" > /dev/null; then
                echo "✅ Process is running"
            else
                echo "⏸️  Process is not running"
            fi
            
            echo ""
            
            # Show progress
            if [ -f "$OUTPUT_FILE" ]; then
                python3 << EOF
import json, os
f = "$OUTPUT_FILE"
data = json.load(open(f))
total = len(data)
bands = sum(1 for x in data if x.get('classification') == 'band')
solo = sum(1 for x in data if x.get('classification') == 'solo')
unknown = sum(1 for x in data if x.get('classification') == 'unknown')
size = os.path.getsize(f) / 1024

print(f"📊 Progress: {total}/1998 ({total*100/1998:.1f}%)")
print(f"   Bands: {bands}")
print(f"   Solo: {solo}")
print(f"   Unknown: {unknown}")
print(f"   File size: {size:.1f} KB")
if total < 1998:
    remaining = (1998 - total) * 0.5 / 60
    print(f"   ⏱️  Estimated remaining: ~{remaining:.1f} minutes")
else:
    print(f"   ✅ COMPLETED!")
EOF
            else
                if [ -f "$LOG_FILE" ]; then
                    count=$(grep -c "\[.*/1998\] Classifying" "$LOG_FILE" 2>/dev/null || echo "0")
                    echo "⏳ File chưa được tạo."
                    echo "   Artists processed (from log): $count/1998"
                else
                    echo "⏳ No progress yet."
                fi
            fi
            
            echo ""
            echo "Last log entries:"
            tail -3 "$LOG_FILE" 2>/dev/null | sed 's/^/   /' || echo "   (no log yet)"
            
            echo ""
            echo "Press Ctrl+C to exit monitor"
            sleep 5
        done
        ;;
    
    *)
        echo "Band Classification Helper Script"
        echo ""
        echo "Usage: ./scripts/run_classification.sh <command>"
        echo ""
        echo "Commands:"
        echo "  start, run      - Run classification with live output (shows progress)"
        echo "  background, bg  - Run classification in background"
        echo "  monitor, watch  - Monitor progress in real-time (all-in-one)"
        echo "  log, tail       - View log file (tail -f)"
        echo "  progress, status - Check current progress (one-time)"
        echo "  stats, statistics - Show final statistics"
        echo "  stop, kill      - Stop running process"
        echo "  test            - Test with sample (10 artists)"
        echo "  test-seed       - Test with seed artists"
        echo ""
        echo "📝 RECOMMENDED WORKFLOW:"
        echo ""
        echo "  Option 1: All-in-one (1 terminal)"
        echo "    ./scripts/run_classification.sh start"
        echo ""
        echo "  Option 2: Background + Monitor (2 terminals)"
        echo "    Terminal 1: ./scripts/run_classification.sh background"
        echo "    Terminal 2: ./scripts/run_classification.sh monitor"
        echo ""
        echo "  Option 3: Background + Check when needed"
        echo "    ./scripts/run_classification.sh background"
        echo "    # Check progress anytime:"
        echo "    ./scripts/run_classification.sh progress"
        echo ""
        echo "Examples:"
        echo "  ./scripts/run_classification.sh start      # Run và xem progress"
        echo "  ./scripts/run_classification.sh background # Run trong background"
        echo "  ./scripts/run_classification.sh monitor     # Monitor real-time"
        echo "  ./scripts/run_classification.sh progress    # Check một lần"
        echo "  ./scripts/run_classification.sh stats      # Xem statistics"
        ;;
esac

