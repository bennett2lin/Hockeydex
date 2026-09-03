# Hockeydex - (https://hockeydex.streamlit.app/)

Live NHL percentile cards and leaderboards for any skater or goalie, any
season since 2008-09, built with Streamlit and MoneyPuck data.

Built by [bennett2lin](https://github.com/bennett2lin).

## What it does

- Search any skater or goalie by full name, first name, or last name
- See a JFresh-style percentile card: 8 key stats for skaters, 4 for
  goalies, each ranked against same-role peers, plus real season totals
  (GP, goals, assists, points, PIM, TOI / save %, GAA)
- Browse a sortable, full-league leaderboard for any season -- click any
  player's name to jump straight to their card
- Pick any season back to 2008-09 from a dropdown; data loads live from
  MoneyPuck, no manual downloads required
- Read a plain-language glossary explaining every stat, directly in the app



## Data source

All stats are fetched live from [MoneyPuck.com](https://moneypuck.com/data.htm)'s
public season-summary CSV exports.
