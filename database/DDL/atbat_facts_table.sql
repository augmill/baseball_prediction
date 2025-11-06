CREATE TABLE IF NOT EXISTS `baseball-prediction-473623.statcast_data.atbat_facts` (
  ------- Game Info -------
  game_id INT64 NOT NULL OPTIONS(description = 'Unique Id for Game.'),
  game_date DATE NOT NULL OPTIONS(description = 'Date of the Game.'),
  game_type STRING NOT NULL OPTIONS(description = 'Type of Game. E = Exhibition, S = Spring Training, R = Regular Season, F = Wild Card, D = Divisional Series, L = League Championship Series, W = World Series'),
  home_team STRING NOT NULL OPTIONS(description = 'Abbreviation of home team.'),
  away_team STRING NOT NULL OPTIONS(description = 'Abbreviation of away team.'),

  ------- At-bat Info -------
  at_bat_number INT64 NOT NULL OPTIONS(description = 'Plate appearance number of the game.'),
  inning INT64 NOT NULL OPTIONS(description = 'Pre-pitch inning number.'),
  inning_topbot STRING NOT NULL OPTIONS(description = 'Pre-pitch top or bottom of inning.'),
  events STRING NOT NULL OPTIONS(description = 'Event of the resulting Plate Appearance.'),

  ------- Batter Info -------  
  batter INT64 NOT NULL OPTIONS(description = 'MLB Player Id tied to the play event.'),
  stand STRING NOT NULL OPTIONS(description = 'Side of the plate batter is standing.'),
  
  ------ Pitcher Info ------
  pitcher INT64 NOT NULL OPTIONS(description = 'MLB Player Id tied to the play event.'),
  p_throws STRING NOT NULL OPTIONS(description = 'Hand pitcher throws with.'),

  ------ Pitch Data ------
  pitches ARRAY<STRUCT<   
    ------ General Info ------
    pitch_type STRING NOT NULL OPTIONS(description = 'The type of pitch derived from Statcast.'),
    pitch_name STRING NOT NULL OPTIONS(description = 'The name of the pitch derived from the Statcast Data.'),
    pitch_number INT64 NOT NULL OPTIONS(description = 'Total pitch number of the plate appearance.'),
    description STRING NOT NULL OPTIONS(description = 'Description of the resulting pitch.'),
    type STRING NOT NULL OPTIONS(description = 'Short hand of pitch result. B = ball, S = strike, X = in play.'),
    sz_top FLOAT64 NOT NULL OPTIONS(description = 'Top of the batters strike zone set by the operator when the ball is halfway to the plate.'),
    sz_bot FLOAT64 NOT NULL OPTIONS(description = 'Bottom of the batters strike zone set by the operator when the ball is halfway to the plate.'),
    des STRING NOT NULL OPTIONS(description = 'Plate appearance description from game day.'),
    
    ------- Pitch Position Info -------
    release_pos_x FLOAT64 NOT NULL OPTIONS(description = 'Horizontal Release Position of the ball measured in feet from the catchers perspective.'),
    release_pos_y FLOAT64 NOT NULL OPTIONS(description = 'Release position of pitch measured in feet from the catchers perspective.'),
    release_pos_z FLOAT64 NOT NULL OPTIONS(description = 'Vertical Release Position of the ball measured in feet from the catchers perspective.'),
    plate_x FLOAT64 NOT NULL OPTIONS(description = 'Horizontal position of the ball when it crosses home plate from the catchers perspective.'),
    plate_z FLOAT64 NOT NULL OPTIONS(description = 'Vertical position of the ball when it crosses home plate from the catchers perspective.'),
    zone INT64 NOT NULL OPTIONS(description = 'Zone location of the ball when it crosses the plate from the catchers perspective.'),

    ------- Pitch Movement Info -------
    release_speed FLOAT64 NOT NULL OPTIONS(description = 'Pitch velocities from 2008-16 are via Pitch F/X, adjusted to roughly out-of-hand release point. All velocities from 2017+ are Statcast, out-of-hand.'),
    effective_speed FLOAT64 NOT NULL OPTIONS(description = 'Derived speed based on the extension of the pitchers release.'),
    vx0 FLOAT64 NOT NULL OPTIONS(description = 'Velocity of the pitch (ft/s) in x-dimension, determined at y=50 feet.'),
    vy0 FLOAT64 NOT NULL OPTIONS(description = 'Velocity of the pitch (ft/s) in y-dimension, determined at y=50 feet.'),
    vz0 FLOAT64 NOT NULL OPTIONS(description = 'Velocity of the pitch (ft/s) in z-dimension, determined at y=50 feet.'),
    ax FLOAT64 NOT NULL OPTIONS(description = 'Acceleration of the pitch (ft/s²) in x-dimension, determined at y=50 feet.'),
    ay FLOAT64 NOT NULL OPTIONS(description = 'Acceleration of the pitch (ft/s²) in y-dimension, determined at y=50 feet.'),
    az FLOAT64 NOT NULL OPTIONS(description = 'Acceleration of the pitch (ft/s²) in z-dimension, determined at y=50 feet.'),
    pfx_x FLOAT64 NOT NULL OPTIONS(description = 'Horizontal movement in feet from the catchers perspective.'),
    pfx_z FLOAT64 NOT NULL OPTIONS(description = 'Vertical movement in feet from the catchers perspective.'),
    release_extension FLOAT64 NOT NULL OPTIONS(description = 'Release extension of pitch in feet as tracked by Statcast.'),
    release_spin INT64 NOT NULL OPTIONS(description = 'Spin rate of pitch tracked by Statcast.'),
    spin_axis INT64 NOT NULL OPTIONS(description = 'Spin Axis in the 2D X-Z plane in degrees (0-360). 180 = pure backspin, 0 = pure topspin.'),

    ------- Game State -----
    balls INT64 NOT NULL OPTIONS(description = 'Pre-pitch number of balls in count.'),
    strikes INT64 NOT NULL OPTIONS(description = 'Pre-pitch number of strikes in count.'),
    outs_when_up INT64 NOT NULL OPTIONS(description = 'Pre-pitch number of outs.'),
    on_3b INT64 OPTIONS(description = 'Pre-pitch MLB Player Id of Runner on 3B.'),
    on_2b INT64 OPTIONS(description = 'Pre-pitch MLB Player Id of Runner on 2B.'),
    on_1b INT64 OPTIONS(description = 'Pre-pitch MLB Player Id of Runner on 1B.'),
    home_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch home score.'),
    away_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch away score.'),
    bat_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch bat team score.'),
    fld_score INT64 NOT NULL OPTIONS(description = 'Pre-pitch field team score.'),
    post_home_score INT64 NOT NULL OPTIONS(description = 'Post-pitch home score.'),
    post_away_score INT64 NOT NULL OPTIONS(description = 'Post-pitch away score.'),
    post_bat_score INT64 NOT NULL OPTIONS(description = 'Post-pitch bat team score.'),
    if_fielding_alignment STRING NOT NULL OPTIONS(description = 'Infield fielding alignment at the time of the pitch.'),
    of_fielding_alignment STRING NOT NULL OPTIONS(description = 'Outfield fielding alignment at the time of the pitch.'),
    
    ------- Hit Info -------
    hit_location INT64 OPTIONS(description = 'Position of first fielder to touch the ball.'),
    bb_type STRING OPTIONS(description = 'Batted ball type, ground_ball, line_drive, fly_ball, popup.'),
    hc_x FLOAT64 OPTIONS(description = 'Hit coordinate X of batted ball.'),
    hc_y FLOAT64 OPTIONS(description = 'Hit coordinate Y of batted ball.'),
    hit_distance INT64 OPTIONS(description = 'Projected hit distance of the batted ball.'),
    launch_speed FLOAT64 OPTIONS(description = 'Exit velocity of the batted ball as tracked by Statcast.'),
    launch_angle INT64 OPTIONS(description = 'Launch angle of the batted ball as tracked by Statcast.'),
    launch_speed_angle INT64 OPTIONS(description = 'Launch speed/angle zone (1-6). 1: Weak, 2: Topped, 3: Under, 4: Flare/Burner, 5: Solid Contact, 6: Barrel.'),
    
    ------- General Stats -------
    woba_value FLOAT64 OPTIONS(description = 'wOBA value based on result of play.'),
    woba_denom INT64 OPTIONS(description = 'wOBA denominator based on result of play.'),
    babip_value INT64 OPTIONS(description = 'BABIP value based on result of play.'),
    iso_value INT64 OPTIONS(description = 'ISO value based on result of play.'),
    estimated_ba_using_speedangle FLOAT64 OPTIONS(description = 'Estimated Batting Avg based on launch angle and exit velocity.'),
    estimated_woba_using_speedangle FLOAT64 OPTIONS(description = 'Estimated wOBA based on launch angle and exit velocity.'),
    delta_home_win_exp FLOAT64 OPTIONS(description = 'Change in Win Expectancy before vs. after the Plate Appearance.'),
    delta_run_exp FLOAT64 OPTIONS(description = 'Change in Run Expectancy before vs. after the Pitch.')
  >> NOT NULL
)
PARTITION BY game_date
CLUSTER BY batter, game_pk
OPTIONS (
  description = 'One row per plate appearance with full pitch sequence in a nested ARRAY<STRUCT>.',
  require_partition_filter = TRUE
);