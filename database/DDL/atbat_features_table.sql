CREATE TABLE IF NOT EXISTS `baseball-prediction-473623.statcast_data.atbat_features` (
  ------- Identifiers -------
  game_id INT64 NOT NULL OPTIONS(description = 'Unique Id for Game.'),
  at_bat_number INT64 NOT NULL OPTIONS(description = 'Plate appearance number of the game.'),
  batter INT64 NOT NULL OPTIONS(description = 'MLB Player Id tied to the play event.'),
  pitcher INT64 NOT NULL OPTIONS(description = 'MLB Player Id tied to the play event.'),

  ------- Processed Date Info -------
  game_date_int INT64 NOT NULL OPTIONS(description = 'Date of the Game converted to integer format (YYYYMMDD).'),
  game_date DATE NOT NULL OPTIONS(description = 'Date of the Game for partitioning.'),

  ------- Binary Features (0/1) -------
  stand INT64 NOT NULL OPTIONS(description = 'Batter stance encoded as binary (0/1).'),
  p_throws INT64 NOT NULL OPTIONS(description = 'Pitcher throws encoded as binary (0/1).'),
  inning_topbot INT64 NOT NULL OPTIONS(description = 'Inning top/bottom encoded as binary (0/1).'),
  events INT64 NOT NULL OPTIONS(description = 'At-bat outcome encoded as categorical integer.'),

  ------- Player Presence Indicators -------
  on_3b INT64 NOT NULL OPTIONS(description = 'Boolean indicator if runner on 3B (0/1).'),
  on_2b INT64 NOT NULL OPTIONS(description = 'Boolean indicator if runner on 2B (0/1).'),
  on_1b INT64 NOT NULL OPTIONS(description = 'Boolean indicator if runner on 1B (0/1).'),

  ------- Hashed Features: Game Type -------
  game_type0 INT64 OPTIONS(description = 'Hashed feature for game_type, dimension 0.'),
  game_type1 INT64 OPTIONS(description = 'Hashed feature for game_type, dimension 1.'),
  game_type2 INT64 OPTIONS(description = 'Hashed feature for game_type, dimension 2.'),
  game_type3 INT64 OPTIONS(description = 'Hashed feature for game_type, dimension 3.'),
  game_type4 INT64 OPTIONS(description = 'Hashed feature for game_type, dimension 4.'),

  ------- Hashed Features: Ball Type -------
  bb_type0 INT64 OPTIONS(description = 'Hashed feature for bb_type, dimension 0.'),
  bb_type1 INT64 OPTIONS(description = 'Hashed feature for bb_type, dimension 1.'),
  bb_type2 INT64 OPTIONS(description = 'Hashed feature for bb_type, dimension 2.'),
  bb_type3 INT64 OPTIONS(description = 'Hashed feature for bb_type, dimension 3.'),

  ------- Hashed Features: Pitch Name -------
  pitch_name0 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 0.'),
  pitch_name1 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 1.'),
  pitch_name2 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 2.'),
  pitch_name3 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 3.'),
  pitch_name4 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 4.'),
  pitch_name5 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 5.'),
  pitch_name6 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 6.'),
  pitch_name7 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 7.'),
  pitch_name8 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 8.'),
  pitch_name9 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 9.'),
  pitch_name10 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 10.'),
  pitch_name11 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 11.'),
  pitch_name12 INT64 OPTIONS(description = 'Hashed feature for pitch_name, dimension 12.'),

  ------- Hashed Features: Pitch Type -------
  type0 INT64 OPTIONS(description = 'Hashed feature for pitch result type, dimension 0.'),
  type1 INT64 OPTIONS(description = 'Hashed feature for pitch result type, dimension 1.'),
  type2 INT64 OPTIONS(description = 'Hashed feature for pitch result type, dimension 2.'),

  ------- Hashed Features: Fielding Alignments -------
  if_fielding_alignment0 INT64 OPTIONS(description = 'Hashed feature for infield alignment, dimension 0.'),
  if_fielding_alignment1 INT64 OPTIONS(description = 'Hashed feature for infield alignment, dimension 1.'),
  if_fielding_alignment2 INT64 OPTIONS(description = 'Hashed feature for infield alignment, dimension 2.'),
  if_fielding_alignment3 INT64 OPTIONS(description = 'Hashed feature for infield alignment, dimension 3.'),

  of_fielding_alignment0 INT64 OPTIONS(description = 'Hashed feature for outfield alignment, dimension 0.'),
  of_fielding_alignment1 INT64 OPTIONS(description = 'Hashed feature for outfield alignment, dimension 1.'),
  of_fielding_alignment2 INT64 OPTIONS(description = 'Hashed feature for outfield alignment, dimension 2.'),
  of_fielding_alignment3 INT64 OPTIONS(description = 'Hashed feature for outfield alignment, dimension 3.'),

  ------- Numerical Features (Preserved from original) -------
  inning INT64 NOT NULL OPTIONS(description = 'Pre-pitch inning number.'),
  pitch_number INT64 NOT NULL OPTIONS(description = 'Total pitch number of the plate appearance.'),
  sz_top FLOAT64 NOT NULL OPTIONS(description = 'Top of the batters strike zone.'),
  sz_bot FLOAT64 NOT NULL OPTIONS(description = 'Bottom of the batters strike zone.'),
  
  ------- Pitch Position Info -------
  release_pos_x FLOAT64 NOT NULL OPTIONS(description = 'Horizontal Release Position of the ball measured in feet.'),
  release_pos_y FLOAT64 NOT NULL OPTIONS(description = 'Release position of pitch measured in feet.'),
  release_pos_z FLOAT64 NOT NULL OPTIONS(description = 'Vertical Release Position of the ball measured in feet.'),
  plate_x FLOAT64 NOT NULL OPTIONS(description = 'Horizontal position of the ball when it crosses home plate.'),
  plate_z FLOAT64 NOT NULL OPTIONS(description = 'Vertical position of the ball when it crosses home plate.'),
  zone INT64 NOT NULL OPTIONS(description = 'Zone location of the ball when it crosses the plate.'),

  ------- Pitch Movement Info -------
  release_speed FLOAT64 NOT NULL OPTIONS(description = 'Pitch velocity at release.'),
  effective_speed FLOAT64 NOT NULL OPTIONS(description = 'Derived speed based on the extension of the pitchers release.'),
  vx0 FLOAT64 NOT NULL OPTIONS(description = 'Velocity of the pitch (ft/s) in x-dimension, determined at y=50 feet.'),
  vy0 FLOAT64 NOT NULL OPTIONS(description = 'Velocity of the pitch (ft/s) in y-dimension, determined at y=50 feet.'),
  vz0 FLOAT64 NOT NULL OPTIONS(description = 'Velocity of the pitch (ft/s) in z-dimension, determined at y=50 feet.'),
  ax FLOAT64 NOT NULL OPTIONS(description = 'Acceleration of the pitch (ft/s²) in x-dimension.'),
  ay FLOAT64 NOT NULL OPTIONS(description = 'Acceleration of the pitch (ft/s²) in y-dimension.'),
  az FLOAT64 NOT NULL OPTIONS(description = 'Acceleration of the pitch (ft/s²) in z-dimension.'),
  pfx_x FLOAT64 NOT NULL OPTIONS(description = 'Horizontal movement in feet from the catchers perspective.'),
  pfx_z FLOAT64 NOT NULL OPTIONS(description = 'Vertical movement in feet from the catchers perspective.'),
  release_extension FLOAT64 NOT NULL OPTIONS(description = 'Release extension of pitch in feet.'),
  release_spin INT64 NOT NULL OPTIONS(description = 'Spin rate of pitch tracked by Statcast.'),
  spin_axis INT64 NOT NULL OPTIONS(description = 'Spin Axis in degrees (0-360).'),

  ------- Game State -------
  balls INT64 NOT NULL OPTIONS(description = 'Pre-pitch number of balls in count.'),
  strikes INT64 NOT NULL OPTIONS(description = 'Pre-pitch number of strikes in count.'),
  outs_when_up INT64 NOT NULL OPTIONS(description = 'Pre-pitch number of outs.'),
  home_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch home score.'),
  away_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch away score.'),
  bat_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch bat team score.'),
  fld_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch field team score.'),
  post_home_score INT64 NOT NULL OPTIONS(description = 'Post-pitch home score.'),
  post_away_score INT64 NOT NULL OPTIONS(description = 'Post-pitch away score.'),
  post_bat_score INT64 NOT NULL OPTIONS(description = 'Post-pitch bat team score.'),

  ------- Additional Numerical Features -------
  iso_value INT64 OPTIONS(description = 'ISO value based on result of play.'),

  ------- Vector Embeddings -------
  embedding_vector ARRAY<FLOAT64> OPTIONS(description = 'Vector embedding representation of the processed at-bat features for ML model training and similarity searches.')

)
PARTITION BY game_date
CLUSTER BY batter, events
OPTIONS (
  description = 'Processed at-bat level data with feature engineering applied, including hashed categorical features and vector embeddings for machine learning.',
  require_partition_filter = TRUE
);