"""
Clean raw Statcast CSV data for downstream processing.
Removes unused columns, normalizes missing values, and ensures data quality.
"""
import pandas as pd
import sys
import os

# Columns to keep based on atbat_facts DDL
COLUMNS_TO_KEEP = [
    # Game Info
    'game_pk',
    'game_date',
    'game_type',
    'home_team',
    'away_team',
    
    # At-bat Info
    'at_bat_number',
    'inning',
    'inning_topbot',
    'events',
    
    # Batter Info
    'batter',
    'stand',
    
    # Pitcher Info
    'pitcher',
    'p_throws',
    
    # Pitch Data - General Info
    'pitch_type',
    'pitch_name',
    'pitch_number',
    'description',
    'type',
    'sz_top',
    'sz_bot',
    'des',
    
    # Pitch Position Info
    'release_pos_x',
    'release_pos_y',
    'release_pos_z',
    'plate_x',
    'plate_z',
    'zone',
    
    # Pitch Movement Info
    'release_speed',
    'effective_speed',
    'vx0',
    'vy0',
    'vz0',
    'ax',
    'ay',
    'az',
    'pfx_x',
    'pfx_z',
    'release_extension',
    'release_spin_rate',
    'spin_axis',
    
    # Game State
    'balls',
    'strikes',
    'outs_when_up',
    'on_3b',
    'on_2b',
    'on_1b',
    'home_score',
    'away_score',
    'bat_score',
    'fld_score',
    'post_home_score',
    'post_away_score',
    'post_bat_score',
    'if_fielding_alignment',
    'of_fielding_alignment',
    
    # Hit Info
    'hit_location',
    'bb_type',
    'hc_x',
    'hc_y',
    'hit_distance_sc',
    'launch_speed',
    'launch_angle',
    'launch_speed_angle',
    
    # General Stats
    'woba_value',
    'woba_denom',
    'babip_value',
    'iso_value',
    'estimated_ba_using_speedangle',
    'estimated_woba_using_speedangle',
    'delta_home_win_exp',
    'delta_run_exp'
]


def clean_data(input_csv, output_csv):
    """
    Clean raw Statcast CSV data.
    
    Args:
        input_csv: Path to raw CSV file
        output_csv: Path to output cleaned CSV file
    """
    print(f"Reading raw data from: {input_csv}")
    
    # Read the CSV, treating first column as index if it's unnamed
    df = pd.read_csv(input_csv, index_col=0 if pd.read_csv(input_csv, nrows=0).columns[0] == '' else None, low_memory=False)
    
    input_rows = len(df)
    input_cols = len(df.columns)
    
    print(f"Input: {input_rows} rows, {input_cols} columns")
    
    # Validate required columns exist
    missing_cols = [col for col in COLUMNS_TO_KEEP if col not in df.columns]
    if missing_cols:
        print(f"WARNING: Missing expected columns: {missing_cols}")
    
    # Keep only the columns we need that actually exist
    cols_to_keep = [col for col in COLUMNS_TO_KEEP if col in df.columns]
    df = df[cols_to_keep]
    
    print(f"Kept {len(cols_to_keep)} columns, dropped {input_cols - len(cols_to_keep)} columns")
    
    # Rename game_pk to game_id for consistency with DDL
    if 'game_pk' in df.columns:
        df = df.rename(columns={'game_pk': 'game_id'})
    
    # Rename hit_distance_sc to hit_distance for consistency with DDL
    if 'hit_distance_sc' in df.columns:
        df = df.rename(columns={'hit_distance_sc': 'hit_distance'})
    
    # Normalize missing values - convert various null representations to empty string
    # pandas will handle these appropriately when writing to CSV
    df = df.replace({
        'NA': None,
        'NaN': None,
        'nan': None,
        'null': None,
        'NULL': None,
        '': None
    })
    
    # Clean text fields - strip whitespace
    text_columns = ['game_type', 'events', 'description', 'stand', 'p_throws', 
                    'home_team', 'away_team', 'type', 'pitch_type', 'pitch_name',
                    'des', 'bb_type', 'inning_topbot', 'if_fielding_alignment', 
                    'of_fielding_alignment']
    
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' string with None
            df.loc[df[col] == 'nan', col] = None
    
    # Ensure numeric fields are parseable - coerce errors to NaN
    numeric_columns = [
        'game_id', 'at_bat_number', 'inning', 'batter', 'pitcher',
        'pitch_number', 'sz_top', 'sz_bot', 'release_pos_x', 'release_pos_y',
        'release_pos_z', 'plate_x', 'plate_z', 'zone', 'release_speed',
        'effective_speed', 'vx0', 'vy0', 'vz0', 'ax', 'ay', 'az',
        'pfx_x', 'pfx_z', 'release_extension', 'release_spin_rate', 'spin_axis',
        'balls', 'strikes', 'outs_when_up', 'on_3b', 'on_2b', 'on_1b',
        'home_score', 'away_score', 'bat_score', 'fld_score',
        'post_home_score', 'post_away_score', 'post_bat_score',
        'hit_location', 'hc_x', 'hc_y', 'hit_distance', 'launch_speed',
        'launch_angle', 'launch_speed_angle', 'woba_value', 'woba_denom',
        'babip_value', 'iso_value', 'estimated_ba_using_speedangle',
        'estimated_woba_using_speedangle', 'delta_home_win_exp', 'delta_run_exp'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with missing critical fields
    required_fields = ['game_id', 'game_date', 'at_bat_number', 'pitch_number', 
                      'batter', 'pitcher', 'inning', 'inning_topbot']
    
    initial_rows = len(df)
    df = df.dropna(subset=[col for col in required_fields if col in df.columns])
    dropped_rows = initial_rows - len(df)
    
    if dropped_rows > 0:
        print(f"Dropped {dropped_rows} rows with missing critical fields")
    
    output_rows = len(df)
    
    # Enforce deterministic column order
    final_column_order = [
        'game_id', 'game_date', 'game_type', 'home_team', 'away_team',
        'at_bat_number', 'inning', 'inning_topbot', 'events',
        'batter', 'stand', 'pitcher', 'p_throws',
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
    
    # Only include columns that exist in the dataframe
    final_column_order = [col for col in final_column_order if col in df.columns]
    df = df[final_column_order]
    
    # Write cleaned CSV
    print(f"Writing cleaned data to: {output_csv}")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    
    # Summary
    print(f"\n=== Cleaning Summary ===")
    print(f"Input rows:    {input_rows}")
    print(f"Output rows:   {output_rows}")
    print(f"Rows dropped:  {input_rows - output_rows}")
    print(f"Columns kept:  {len(final_column_order)}")
    print(f"Columns dropped: {input_cols - len(final_column_order)}")
    print(f"Output file:   {output_csv}")
    

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 CleanData.py <input_raw_csv> <output_clean_csv>")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    
    if not os.path.exists(input_csv):
        print(f"Error: Input file not found: {input_csv}")
        sys.exit(1)
    
    try:
        clean_data(input_csv, output_csv)
        print("\n✓ Cleaning completed successfully")
    except Exception as e:
        print(f"\n✗ Error during cleaning: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

