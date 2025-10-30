CREATE TABLE IF NOT EXISTS `baseball-prediction-473623.statcast_data.batter_dim` (
    player_id INT64 NOT NULL,
    player_name STRING NOT NULL,
    birthday DATE NOT NULL,
    seasonal_stats ARRAY<STRUCT<
        season_year INT64 NOT NULL,
        team STRING NOT NULL,
        plate_apperances INT64 NOT NULL,
        atbats INT64 NOT NULL,
        hits INT64 NOT NULL,
        home_runs INT64 NOT NULL,
        rbi INT64  NOT NULL,
        batting_avg FLOAT64 NOT NULL,
        obp FLOAT64 NOT NULL,
        slg FLOAT64 NOT NULL,
        ops FLOAT64 NOT NULL,
        woba FLOAT64 NOT NULL,
        avg_exit_vel FLOAT64 NOT NULL,
    >>
)
CLUSTER BY player_id
OPTIONS (
  description = 'Batter dimension with precomputed seasonal aggregates.'
);