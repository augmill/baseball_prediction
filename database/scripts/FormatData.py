"""
Format cleaned Statcast CSV into nested JSONL for BigQuery ingestion.
Groups individual pitch records into per-at-bat objects with nested pitches array.
"""
import pandas as pd
import json
import sys
import os


def format_data(input_clean_csv, output_jsonl):
    """
    Convert cleaned per-day Statcast CSV into nested JSONL file.
    
    Args:
        input_clean_csv: Path to cleaned CSV file
        output_jsonl: Path to output JSONL file
    """
    print(f"Reading cleaned data from: {input_clean_csv}")
    
    df = pd.read_csv(input_clean_csv, low_memory=False)
    
    total_pitches = len(df)
    print(f"Loaded {total_pitches} pitch records")
    
    # At-bat level columns (non-pitch specific)
    atbat_columns = [
        'game_id', 'game_date', 'game_type', 'home_team', 'away_team',
        'at_bat_number', 'inning', 'inning_topbot', 'events',
        'batter', 'stand', 'pitcher', 'p_throws'
    ]
    
    # Pitch-level columns (will go into pitches array)
    pitch_columns = [
        'pitch_type', 'pitch_name', 'pitch_number', 'description', 'type',
        'sz_top', 'sz_bot', 'des',
        'release_pos_x', 'release_pos_y', 'release_pos_z', 'plate_x', 'plate_z', 'zone',
        'release_speed', 'effective_speed', 'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az',
        'pfx_x', 'pfx_z', 'release_extension', 'release_spin_rate', 'spin_axis',
        'balls', 'strikes', 'outs_when_up', 'on_3b', 'on_2b', 'on_1b',
        'home_score', 'away_score', 'bat_score', 'fld_score',
        'post_home_score', 'post_away_score', 'post_bat_score',
        'if_fielding_alignment', 'of_fielding_alignment',
        'hit_location', 'bb_type', 'hc_x', 'hc_y', 'hit_distance',
        'launch_speed', 'launch_angle', 'launch_speed_angle',
        'woba_value', 'woba_denom', 'babip_value', 'iso_value',
        'estimated_ba_using_speedangle', 'estimated_woba_using_speedangle',
        'delta_home_win_exp', 'delta_run_exp'
    ]
    
    # Group by game_id and at_bat_number
    grouped = df.groupby(['game_id', 'at_bat_number'])
    
    at_bats_processed = 0
    at_bats_dropped = 0
    
    results = []
    
    for (game_id, at_bat_number), group in grouped:
        # Filter: Drop at-bats with multiple pitchers
        unique_pitchers = group['pitcher'].nunique()
        if unique_pitchers > 1:
            at_bats_dropped += 1
            continue
        
        # Check for required fields
        if group[['pitcher', 'batter']].isnull().any().any():
            at_bats_dropped += 1
            continue
        
        # Check if events is null (required field)
        if pd.isna(group['events'].iloc[0]):
            at_bats_dropped += 1
            continue
        
        # Build at-bat level data (take first row since they're all the same for the at-bat)
        at_bat_data = {}
        for col in atbat_columns:
            if col in group.columns:
                val = group[col].iloc[0]
                # Convert to native Python type and handle NaN
                if pd.isna(val):
                    at_bat_data[col] = None
                elif isinstance(val, (pd.Int64Dtype, pd.Int32Dtype)) or col in ['game_id', 'at_bat_number', 'inning', 'batter', 'pitcher']:
                    at_bat_data[col] = int(val) if not pd.isna(val) else None
                else:
                    at_bat_data[col] = val
        
        # Build pitches array - sort by pitch_number
        pitches = []
        for _, pitch_row in group.sort_values('pitch_number').iterrows():
            pitch_data = {}
            
            # Skip pitches with missing required NOT NULL fields
            required_pitch_fields = [
                'pitch_type', 'pitch_name', 'pitch_number', 'description', 'type',
                'sz_top', 'sz_bot', 'des', 'release_pos_x', 'release_pos_y', 'release_pos_z',
                'plate_x', 'plate_z', 'zone', 'release_speed', 'effective_speed',
                'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az', 'pfx_x', 'pfx_z',
                'release_extension', 'release_spin_rate', 'spin_axis',
                'balls', 'strikes', 'outs_when_up', 'home_score', 'away_score',
                'bat_score', 'fld_score', 'post_home_score', 'post_away_score', 'post_bat_score',
                'if_fielding_alignment', 'of_fielding_alignment'
            ]
            
            skip_pitch = False
            for req_field in required_pitch_fields:
                if req_field in pitch_row.index and pd.isna(pitch_row[req_field]):
                    skip_pitch = True
                    break
            
            if skip_pitch:
                continue
            
            for col in pitch_columns:
                if col in pitch_row.index:
                    val = pitch_row[col]
                    # Rename release_spin_rate to release_spin for BQ schema
                    output_col = 'release_spin' if col == 'release_spin_rate' else col
                    # Convert to native Python type and handle NaN
                    if pd.isna(val):
                        pitch_data[output_col] = None
                    elif col in ['pitch_number', 'zone', 'release_spin_rate', 'spin_axis', 
                                'balls', 'strikes', 'outs_when_up', 'on_3b', 'on_2b', 'on_1b',
                                'home_score', 'away_score', 'bat_score', 'fld_score',
                                'post_home_score', 'post_away_score', 'post_bat_score',
                                'hit_location', 'hit_distance', 'launch_angle', 'launch_speed_angle',
                                'woba_denom', 'babip_value', 'iso_value']:
                        pitch_data[output_col] = int(val) if not pd.isna(val) else None
                    elif col in ['sz_top', 'sz_bot', 'release_pos_x', 'release_pos_y', 'release_pos_z',
                                'plate_x', 'plate_z', 'release_speed', 'effective_speed',
                                'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az', 'pfx_x', 'pfx_z',
                                'release_extension', 'hc_x', 'hc_y', 'launch_speed',
                                'woba_value', 'estimated_ba_using_speedangle', 
                                'estimated_woba_using_speedangle', 'delta_home_win_exp', 'delta_run_exp']:
                        pitch_data[output_col] = float(val) if not pd.isna(val) else None
                    else:
                        pitch_data[output_col] = val if not pd.isna(val) else None
            
            pitches.append(pitch_data)
        
        # Combine at-bat data with pitches array
        at_bat_data['pitches'] = pitches
        results.append(at_bat_data)
        at_bats_processed += 1
    
    # Write JSONL output
    print(f"Writing formatted data to: {output_jsonl}")
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    
    with open(output_jsonl, 'w') as f:
        for record in results:
            f.write(json.dumps(record) + '\n')
    
    # Summary
    print(f"\n=== Formatting Summary ===")
    print(f"Total pitches:       {total_pitches}")
    print(f"At-bats processed:   {at_bats_processed}")
    print(f"At-bats dropped:     {at_bats_dropped}")
    print(f"Output file:         {output_jsonl}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 FormatData.py <input_clean_csv> <output_jsonl>")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_jsonl = sys.argv[2]
    
    if not os.path.exists(input_csv):
        print(f"Error: Input file not found: {input_csv}")
        sys.exit(1)
    
    try:
        format_data(input_csv, output_jsonl)
        print("\n✓ Formatting completed successfully")
    except Exception as e:
        print(f"\n✗ Error during formatting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
