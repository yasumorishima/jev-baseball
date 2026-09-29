# One row per ABS pitch challenge (reviewType "MJ" = challenge of a pitch result).
# Count, outs and score are taken from BEFORE the challenged pitch.
# NOTE: `call` is the FINAL call after the review (it reflects the outcome); the
# original call must be derived from which side challenged (batting side challenges
# strikes, fielding side challenges balls) -- never show `call` to a model.
.gameData as $g
| .liveData.plays.allPlays as $plays
| range(0; $plays | length) as $k
| $plays[$k] as $p
| ($p.playEvents) as $ev
| range(0; $ev | length) as $i
| $ev[$i]
| select(.reviewDetails.reviewType == "MJ")
| ([$ev[0:$i][] | select(.count != null)] | last | .count) as $prev
| (if $k == 0 then {homeScore: 0, awayScore: 0} else $plays[$k - 1].result end) as $sc
| {
    date: $date,
    gamePk: $g.game.pk,
    inning: $p.about.inning,
    half: $p.about.halfInning,
    home: $g.teams.home.abbreviation,
    away: $g.teams.away.abbreviation,
    home_id: $g.teams.home.id,
    away_id: $g.teams.away.id,
    home_score_before: $sc.homeScore,
    away_score_before: $sc.awayScore,
    balls: ($prev.balls // 0),
    strikes: ($prev.strikes // 0),
    outs: ($prev.outs // (.count.outs)),
    call: .details.call.description,
    pitch_type: .details.type.code,
    speed: .pitchData.startSpeed,
    pX: .pitchData.coordinates.pX,
    pZ: .pitchData.coordinates.pZ,
    sz_top: .pitchData.strikeZoneTop,
    sz_bot: .pitchData.strikeZoneBottom,
    overturned: .reviewDetails.isOverturned,
    challenge_team: .reviewDetails.challengeTeamId,
    challenger_id: .reviewDetails.player.id,
    challenger: .reviewDetails.player.fullName,
    batter_id: $p.matchup.batter.id,
    pitcher_id: $p.matchup.pitcher.id,
    batting_team_is_home: ($p.about.halfInning == "bottom")
  }
