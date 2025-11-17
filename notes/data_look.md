# data look thorugh

| column | note | type | convert needed | level |
| :---- | :---- | :---- | :---- | :---- |
| ~~Unnamed 0~~ | | | | |
| *pitch_type* | from statcast | nominal | yes| pitch |
| game_date | | interval | yes | pitch |
| release_speed | | ratio | no | pitch |
| release_pos_x | | ratio | no | pitch |
| release_pos_z | | ratio | no | pitch |
| *player_name* | | nominal | yes | pitch |
| *batter* | | nominal | yes | pitch |
| *pitcher* | | nominal | yes | pitch |
| events | at-bat outcome | nominal | yes | at-bat|
| description | pitch outcome | nominal | yes | pitch |
| ~~spin_dir~~ | | | | |
| ~~spin_rate_deprecated~~ |||||
|~~break_angle_deprecated~~ |||||
|~~break_length_deprecated~~|||||
|zone||ordinal? or nominal| no | pitch |
|des | natural language | string | | at-bat for full sent, pitch for any |
|game_type| E = Exhibition  S = Spring Training  R = Regular Season  F = Wild Card  D = Divisional Series  L = League Championship Series  W = World Series| nominal | yes | pitch |
| stand| side of plate batter is on | binary | yes| pitch |
|p_throws | hand of pitcher | binary | yes| pitch |
|*home_team*| | nominal | yes| pitch|
|*away_team*| | nominal | yes| pitch|
|type| short hand pitch result B = ball, S = strike, X = in play | nominal | yes| pitch|
|hit_location| position of first fielder to touch the ball | nominal | no| at-bat (not all have one) |
| bb_type| Batted ball type, ground_ball, line_drive, fly_ball, popup | nominal | yes | at-bat (not all have one)|
|balls| | ordinal | no | pitch |
| strikes | | ordinal | no | pitch |
|game_year | | interval | no | pitch|
| pfx_x | horizontal movement in feet from the catcher's perspective | interval | no | pitch |
|pfx_z| vertical ^ | interval | no| pitch|
|plate_x| horizontal position of the ball when it crosses home plate from the catcher's perspective | interval | no| pitch |
|plate_z| vertical ^ | interval | no| pitch |
|*on_3b*| player id of player on 3rd | nominal | yes (could make binary)| pitch |
|*on_2b*| ^ on 2nd | nominal | yes | pitch |
|*on_1b*| ^ on 1st | nominal | yes | pitch |
|outs_when_up | number of outs before pitch | ordinal | no | pitch |
|inning | | ordinal | no | pitch |
|inning_topbot | | binary | yes| pitch |
|hc_x| hit x coordinate of batted ball | ratio | no | at_bat (not all have one)|
|hc_y | hit y ^ | ratio | no | at-bat ^ |
|~~tfs_deprecated~~|||||
|~~tfs_zulu_deprecated~~|||||
|~~umpire~~|||||
|*sv_id*| Non-unique Id of play event per game||||
|vx0| x-dim pitch velocity in f/s | ratio | no | pitch |
|vy0| y-dim ^ | ratio | no | pitch |
|vz0| z-dim ^ | ratio | no | pitch |
|ax| x-dim pitch acceleration in f/s| ratio | no | pitch|
|ay| y-dim pitch acceleration in f/s| ratio | no | pitch|
|az| z-dim pitch acceleration in f/s| ratio | no | pitch|
|sz_top| Top of the batter's strike zone set by the operator when the ball is halfway to the plate| ratio | no | pitch |
|sz_bot| bottom ^ | ratio | no | pitch |
|hit_distance_sc| projected distance | ratio | no | pitch (not all have one)|
|launch_speed| | ratio | no | pitch (not all have one) |
|launch_angle || ratio | no |pitch (not all have one)|
|effective_speed| Derived speed based on the the extension of the pitcher's release. | ratio | no | pitch |
|release_spin_rate| of pitch tracked by statcast | ratio | no | pitch |
|release_extension| Release extension of pitch in feet as tracked by Statcast. | ratio | no | pitch |
|*game_pk*| game id | unkown | unknown | pitch |
|~~fielder_2:9~~| player ids of fielders| nominal | yes | pitch|
|release_pos_y| Release position of pitch measured in feet from the catcher's perspective. | ratio or interval | no | pitch|
|*estimated_ba_using_speedangle*| Estimated Batting Avg based on launch angle and exit velocity. | ratio | no | pitch (not all have one) |
|*estimated_woba_using_speedangle*| (weighted on base average) Estimated wOBA based on launch angle and exit velocity. | ratio | no | pitch (not all have one) |
|*woba_value*| (weighted on base average) wOBA value based on result of play. | ratio | no | pitch (not all have one) |
|*woba_denom* | (weighted on base average) wOBA denominator based on result of play. | ratio | no | pitch (not all have one) |
|babip_value | batting average on balls in play based on result of play| ratio | no | pitch (not all have one) |
|iso_value | isolated power | ratio | no | pitch (not all have one) |
|launch_speed_angle | Launch speed/angle zone based on launch angle and exit velocity. 1: Weak 2: Topped 3: Under 4: Flare/Burner 5: Solid Contact 6: Barrel| nominal | yes |  pitch (not all have one) |
|at_bat_number| plate appearance number of the game | ratio | no | pitch |
|pitch_number| for plate appearance | ratio | no | pitch|
|pitch_name| from statcast | nominal | yes | pitch |
|home_score| | ratio | no | pitch |
|away_score| | ratio | no | pitch |
|bat_score| bat team score | ratio | no | pitch |
|fld_score| field team score | ratio | no | pitch |
|post_away_score| post pitch | ratio | no | pitch |
|post_home_score| ^ | ratio | no | pitch |
|post_bat_score| ^ | ratio | no | pitch |
|post_fld_score| ^ | ratio | no | pitch |
|if_fielding_alignment| infield alignment | nominal | yes | pitch |
|of_fielding_alignment | outfield alignment | nominal | yes | pitch |
|spin_axis| axis in 2d x-z plane, such that 180 represents a pure backspin fastball and 0 degrees represents a pure topspin (12-6) curveball | interval | no | pitch |
|*delta_home_win_exp*| change in Win Expectancy before the Plate Appearance and after the Plate Appearance | ratio | no | pitch|
|*delta_run_exp*| change in Run Expectancy before the Pitch and after the Pitch | ratio | no | pitch |
|*bat_speed*| not on savant page| |||
|*swing_length*| not on savant page| |||
|*estimated_slg_using_speedangle*| slugging percent, not on savant page| ratio |no|pitch (not all has one)|
|*delta_pitcher_run_exp*| not on savant page| ratio | no |pitch |
|hyper_speed| not on savant page| ||picth (not all has one)|
|home_score_diff| not on savant page| |no|pitch|
|bat_score_diff| not on savant page|  |no|pitch|
|home_win_exp| not on savant page, maybe expected win percent or odds for home team| | no | pitch|
|bat_win_exp| not on savant page, ^ for bat team| | no | pitch|
|age_pit_legacy| not on savant page| ratio | no | pitch |
|age_bat_legacy| not on savant page| ratio | no | pitch|
|age_pit| not on savant page| ratio | no | pitch |
|age_bat| not on savant page| ratio | no | pitch |
|n_thruorder_pitcher| not on savant page could refer to if it is at least the thrid time the batter has gone against pitcher in this game or in general| | no | pitch |
|n_priorpa_thisgame_player_at_bat| not on savant page but could be number of prior plate appearances this game| | no | pitch |
|pitcher_days_since_prev_game| not on savant page| ratio or ordianl | no | pitch|
|batter_days_since_prev_game| not on savant page| ratio or ordinal | no | pitch |
|*pitcher_days_until_next_game*| not on savant page| ratio or ordinal | no | pitch |
|*batter_days_until_next_game*| not on savant page| ratio or ordinal | no | pitch |
|*api_break_z_with_gravity*| not on savant page| | no | pitch |
|*api_break_x_arm*| |  | no |pitch|
|*api_break_x_batter_in*| |  | no |pitch|
|*arm_angle*| not on savant page| |||
|*attack_angle*| not on savant page||||
|*attack_direction*| not on savant page||||
|*swing_path_tilt*| not on savant page||||
|*intercept_ball_minus_batter_pos_x_inches*| not on savant page||||
|*intercept_ball_minus_batter_pos_y_inches*| not on savant page||||
