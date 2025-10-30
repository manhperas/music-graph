#!/usr/bin/env python3
"""Improve song coverage for multi-artist albums to reach ≥40%"""

import json
import os
import sys
import time
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from scripts.extract_songs import extract_songs_from_albums_file, SongExtractor
from src.data_collection.utils import logger, log_progress


def analyze_current_coverage():
    """Analyze current song coverage for multi-artist albums"""
    
    # Load albums
    albums_file = "data/processed/albums.json"
    logger.info(f"Loading albums from {albums_file}...")
    with open(albums_file, 'r', encoding='utf-8') as f:
        albums_data = json.load(f)
    
    # Load songs
    songs_file = "data/processed/songs.json"
    existing_songs = {}
    if os.path.exists(songs_file):
        logger.info(f"Loading songs from {songs_file}...")
        with open(songs_file, 'r', encoding='utf-8') as f:
            existing_songs = json.load(f)
    
    # Find multi-artist albums (≥2 artists)
    multi_artist_albums = {}
    single_artist_albums = {}
    
    for album_name, artist_ids in albums_data.items():
        if len(artist_ids) >= 2:
            multi_artist_albums[album_name] = artist_ids
        else:
            single_artist_albums[album_name] = artist_ids
    
    # Check which multi-artist albums have songs
    multi_artist_with_songs = []
    multi_artist_without_songs = []
    
    for album_name in multi_artist_albums:
        songs = existing_songs.get(album_name, [])
        # Filter out empty/invalid songs
        valid_songs = [s for s in songs if s.get('title') and len(s.get('title', '').strip()) > 2]
        
        if valid_songs:
            multi_artist_with_songs.append(album_name)
        else:
            multi_artist_without_songs.append(album_name)
    
    # Calculate statistics
    total_albums = len(albums_data)
    total_multi_artist = len(multi_artist_albums)
    total_single_artist = len(single_artist_albums)
    multi_artist_with_songs_count = len(multi_artist_with_songs)
    multi_artist_without_songs_count = len(multi_artist_without_songs)
    
    current_percentage = (multi_artist_with_songs_count / total_multi_artist * 100) if total_multi_artist > 0 else 0
    target_percentage = 40.0
    target_count = int(total_multi_artist * target_percentage / 100)
    needed_count = max(0, target_count - multi_artist_with_songs_count)
    
    # Print report
    logger.info("=" * 60)
    logger.info("SONG COVERAGE ANALYSIS")
    logger.info("=" * 60)
    logger.info(f"Tổng số albums: {total_albums:,}")
    logger.info(f"  - Single-artist albums (< 2 artists): {total_single_artist:,}")
    logger.info(f"  - Multi-artist albums (≥ 2 artists): {total_multi_artist:,}")
    logger.info("")
    logger.info(f"Albums có songs:")
    logger.info(f"  - Tổng số albums có songs: {sum(1 for v in existing_songs.values() if v and any(s.get('title') and len(s.get('title', '').strip()) > 2 for s in v))}")
    logger.info(f"  - Multi-artist albums có songs: {multi_artist_with_songs_count}/{total_multi_artist}")
    logger.info("")
    logger.info(f"Success Criteria:")
    logger.info(f"  - Hiện tại: {current_percentage:.2f}% ({multi_artist_with_songs_count}/{total_multi_artist})")
    logger.info(f"  - Target: ≥{target_percentage}%")
    logger.info(f"  - Cần thêm: {needed_count} albums để đạt {target_percentage}%")
    
    if needed_count > 0:
        logger.info("")
        logger.info(f"Status: ❌ Chưa đạt (cần thêm ~{needed_count} albums)")
    else:
        logger.info("")
        logger.info(f"Status: ✅ Đã đạt mục tiêu ≥{target_percentage}%")
    
    return {
        'multi_artist_albums': multi_artist_albums,
        'multi_artist_with_songs': multi_artist_with_songs,
        'multi_artist_without_songs': multi_artist_without_songs,
        'current_percentage': current_percentage,
        'target_percentage': target_percentage,
        'needed_count': needed_count,
        'total_multi_artist': total_multi_artist
    }


def improve_coverage(analysis_result: Dict, max_albums_to_extract: int = None):
    """Extract songs from albums without songs to improve coverage"""
    
    albums_without_songs = analysis_result['multi_artist_without_songs']
    needed_count = analysis_result['needed_count']
    
    if needed_count <= 0:
        logger.info("✅ Đã đạt mục tiêu ≥40%, không cần extract thêm")
        return
    
    # Load albums data for sorting
    albums_file = "data/processed/albums.json"
    with open(albums_file, 'r', encoding='utf-8') as f:
        albums_data = json.load(f)
    
    # Determine how many albums to extract
    # Extract more than needed to account for failures (many albums may not have Wikipedia pages)
    # Try 3-5x more albums to increase success rate
    if max_albums_to_extract:
        # User specified max albums - use that (but ensure it's reasonable)
        albums_to_extract = min(max_albums_to_extract, len(albums_without_songs))
    else:
        # Auto-calculate: extract at least 3x needed, minimum 10
        albums_to_extract = max(needed_count * 3, 10)
        # But don't exceed available albums
        albums_to_extract = min(albums_to_extract, len(albums_without_songs))
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("EXTRACTING SONGS TO IMPROVE COVERAGE")
    logger.info("=" * 60)
    logger.info(f"Sẽ extract songs từ {albums_to_extract} albums chưa có songs")
    logger.info(f"Tổng số albums chưa có songs: {len(albums_without_songs)}")
    
    # Extract songs
    extractor = SongExtractor()
    
    # Load existing songs to skip
    songs_file = "data/processed/songs.json"
    existing_songs = {}
    if os.path.exists(songs_file):
        with open(songs_file, 'r', encoding='utf-8') as f:
            existing_songs = json.load(f)
    
    # Select albums to extract
    # Prioritize albums with more artists and common/popular album names
    # Sort by artist count first, then try to pick diverse set
    albums_sorted = sorted(albums_without_songs, key=lambda x: len(albums_data[x]), reverse=True)
    
    # Extract more than needed to account for failures
    albums_to_process = albums_sorted[:albums_to_extract]
    
    logger.info(f"Albums sẽ được extract:")
    for i, album in enumerate(albums_to_process[:15], 1):
        artist_count = len(albums_data[album])
        logger.info(f"  {i}. {album} ({artist_count} artists)")
    if len(albums_to_process) > 15:
        logger.info(f"  ... và {len(albums_to_process) - 15} albums khác")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("BẮT ĐẦU EXTRACT SONGS...")
    logger.info("=" * 60)
    
    # Extract songs với logging chi tiết
    extractor = SongExtractor()
    
    # Load existing songs to skip
    songs_file = "data/processed/songs.json"
    existing_songs = {}
    if os.path.exists(songs_file):
        with open(songs_file, 'r', encoding='utf-8') as f:
            existing_songs = json.load(f)
    
    # Track progress
    results = existing_songs.copy() if existing_songs else {}
    successful_albums = []
    failed_albums = []
    
    start_time = time.time()
    
    for i, album_name in enumerate(albums_to_process, 1):
        logger.info("")
        logger.info("-" * 60)
        logger.info(f"[{i}/{len(albums_to_process)}] Đang extract: {album_name}")
        logger.info(f"   Progress: {i}/{len(albums_to_process)} ({i/len(albums_to_process)*100:.1f}%)")
        
        # Log time estimate
        if i > 1:
            elapsed = time.time() - start_time
            avg_time = elapsed / (i - 1)
            remaining = avg_time * (len(albums_to_process) - i + 1)
            logger.info(f"   Thời gian: {elapsed/60:.1f}m đã qua, ~{remaining/60:.1f}m còn lại")
        
        # Extract songs
        songs = extractor.extract_songs_from_album(album_name)
        
        if songs:
            # Filter valid songs
            valid_songs = [s for s in songs if s.get('title') and len(s.get('title', '').strip()) > 2]
            
            if valid_songs:
                results[album_name] = songs
                successful_albums.append(album_name)
                logger.info(f"   ✅ THÀNH CÔNG: Tìm thấy {len(valid_songs)} songs từ '{album_name}'")
                logger.info(f"   📊 Tổng albums thành công: {len(successful_albums)}/{i}")
                
                # Check if we've reached target
                if len(successful_albums) >= needed_count:
                    logger.info("")
                    logger.info("🎯 ĐÃ ĐẠT SỐ LƯỢNG CẦN THIẾT!")
                    logger.info(f"   Cần: {needed_count} albums")
                    logger.info(f"   Đã có: {len(successful_albums)} albums")
                    logger.info(f"   Tiếp tục extract để đảm bảo chất lượng...")
            else:
                failed_albums.append(album_name)
                logger.warning(f"   ✗ KHÔNG THÀNH CÔNG: Tìm thấy {len(songs)} songs nhưng không hợp lệ")
        else:
            failed_albums.append(album_name)
            logger.warning(f"   ✗ KHÔNG THÀNH CÔNG: Không tìm thấy songs")
        
        # Log progress summary every 5 albums
        if i % 5 == 0 or i == len(albums_to_process):
            logger.info("")
            logger.info("📈 TÓM TẮT TIẾN TRÌNH:")
            logger.info(f"   ✅ Thành công: {len(successful_albums)}/{i} ({len(successful_albums)/i*100:.1f}%)")
            logger.info(f"   ✗ Thất bại: {len(failed_albums)}/{i} ({len(failed_albums)/i*100:.1f}%)")
            logger.info(f"   ⏱️  Đã xử lý: {i}/{len(albums_to_process)} ({i/len(albums_to_process)*100:.1f}%)")
            
            if len(successful_albums) > 0:
                logger.info(f"   🎵 Albums thành công: {', '.join(successful_albums[:3])}")
                if len(successful_albums) > 3:
                    logger.info(f"      ... và {len(successful_albums) - 3} albums khác")
    
    # Save results
    logger.info("")
    logger.info("=" * 60)
    logger.info("LƯU KẾT QUẢ...")
    logger.info("=" * 60)
    extractor.save_songs(results, songs_file)
    
    # Log final summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("KẾT QUẢ EXTRACT SONGS")
    logger.info("=" * 60)
    logger.info(f"Tổng số albums đã xử lý: {len(albums_to_process)}")
    logger.info(f"✅ Albums thành công: {len(successful_albums)}")
    logger.info(f"✗ Albums thất bại: {len(failed_albums)}")
    
    if successful_albums:
        logger.info("")
        logger.info("Albums đã extract thành công:")
        for i, album in enumerate(successful_albums, 1):
            song_count = len(results.get(album, []))
            logger.info(f"  {i}. {album} ({song_count} songs)")
    
    if failed_albums and len(failed_albums) <= 10:
        logger.info("")
        logger.info("Albums không tìm thấy songs:")
        for i, album in enumerate(failed_albums[:10], 1):
            logger.info(f"  {i}. {album}")
    
    # Update CSV
    logger.info("")
    logger.info("=" * 60)
    logger.info("CẬP NHẬT SONGS.CSV...")
    logger.info("=" * 60)
    from scripts.extract_songs import create_song_nodes_csv
    create_song_nodes_csv(
        songs_file=songs_file,
        albums_file="data/processed/albums.json",
        output_file="data/processed/songs.csv"
    )
    
    # Re-analyze
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHÂN TÍCH LẠI COVERAGE...")
    logger.info("=" * 60)
    new_analysis = analyze_current_coverage()
    
    if new_analysis['current_percentage'] >= 40.0:
        logger.info("")
        logger.info("🎉 ĐÃ ĐẠT MỤC TIÊU ≥40%!")
        logger.info(f"   Coverage: {new_analysis['current_percentage']:.2f}%")
        total_multi = new_analysis['total_multi_artist']
        with_songs = len([a for a in new_analysis['multi_artist_albums'] 
                         if a in new_analysis['multi_artist_with_songs']])
        logger.info(f"   Multi-artist albums có songs: {with_songs}/{total_multi}")
    else:
        logger.info("")
        logger.info(f"⚠️  CHƯA ĐẠT MỤC TIÊU")
        logger.info(f"   Coverage hiện tại: {new_analysis['current_percentage']:.2f}%")
        total_multi = new_analysis['total_multi_artist']
        with_songs = len(new_analysis['multi_artist_with_songs'])
        logger.info(f"   Multi-artist albums có songs: {with_songs}/{total_multi}")
        logger.info(f"   Còn thiếu: {new_analysis['needed_count']} albums")
        logger.info("")
        logger.info("💡 Gợi ý: Chạy lại với --max-albums lớn hơn để extract thêm")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Improve song coverage for multi-artist albums')
    parser.add_argument(
        '--max-albums',
        type=int,
        default=None,
        help='Maximum number of albums to extract (default: auto-calculate)'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze, do not extract songs'
    )
    
    args = parser.parse_args()
    
    # Analyze current coverage
    analysis = analyze_current_coverage()
    
    # Extract songs if needed
    if not args.analyze_only:
        improve_coverage(analysis, max_albums_to_extract=args.max_albums)

