"""
app.py -- Hockeydex, by bennett2lin.
"""
import io
import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def fetch_csv(url: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HockeyPercentileApp/1.0)"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text))


@st.cache_data(ttl=3600)
def build_percentiles(csv_path, min_gp=20):
    df = fetch_csv(csv_path)
    df['games_played'] = pd.to_numeric(df['games_played'], errors='coerce')
    df = df.dropna(subset=['games_played'])
    df = df[df['games_played'] >= min_gp]
    df['position_group'] = df['position'].apply(lambda p: 'F' if p in ['C', 'R', 'L'] else 'D')

    ev = df[df['situation'] == '5on5'].copy()
    ev = ev[ev['icetime'] >= 300].copy()
    ev['points'] = ev['I_F_goals'] + ev['I_F_primaryAssists'] + ev['I_F_secondaryAssists']
    ev['points_per60'] = ev['points'] / ev['icetime'] * 3600
    ev['ev_offence_pctl'] = ev.groupby('position_group')['points_per60'].rank(pct=True) * 100

    ev['oi_xga_per60'] = ev['OnIce_A_xGoals'] / ev['icetime'] * 3600
    ev['ev_defence_pctl'] = 100 - (ev.groupby('position_group')['oi_xga_per60'].rank(pct=True) * 100)

    ev['goals_per60'] = ev['I_F_goals'] / ev['icetime'] * 3600
    ev['goals_pctl'] = ev.groupby('position_group')['goals_per60'].rank(pct=True) * 100

    ev['a1_per60'] = ev['I_F_primaryAssists'] / ev['icetime'] * 3600
    ev['a1_pctl'] = ev.groupby('position_group')['a1_per60'].rank(pct=True) * 100

    ev['finishing_raw'] = (ev['I_F_goals'] - ev['I_F_xGoals']) / ev['icetime'] * 3600
    ev['finishing_pctl'] = ev.groupby('position_group')['finishing_raw'].rank(pct=True) * 100

    ev['net_pens_per60'] = (ev['penaltiesDrawn'] - ev['penalties']) / ev['icetime'] * 3600
    ev['penalties_pctl'] = ev.groupby('position_group')['net_pens_per60'].rank(pct=True) * 100

    pp = df[df['situation'] == '5on4'].copy()
    pp = pp[pp['icetime'] >= 30].copy()
    pp['pp_points'] = pp['I_F_goals'] + pp['I_F_primaryAssists'] + pp['I_F_secondaryAssists']
    pp['pp_points_per60'] = pp['pp_points'] / pp['icetime'] * 3600
    pp['pp_pctl'] = pp.groupby('position_group')['pp_points_per60'].rank(pct=True) * 100

    pk = df[df['situation'] == '4on5'].copy()
    pk = pk[pk['icetime'] >= 30].copy()
    pk['pk_xga_per60'] = pk['OnIce_A_xGoals'] / pk['icetime'] * 3600
    pk['pk_pctl'] = 100 - (pk.groupby('position_group')['pk_xga_per60'].rank(pct=True) * 100)

    result = ev[['playerId', 'name', 'team', 'position', 'position_group', 'games_played',
                 'ev_offence_pctl', 'ev_defence_pctl', 'goals_pctl',
                 'a1_pctl', 'finishing_pctl', 'penalties_pctl']].copy()
    result = result.merge(pp[['playerId', 'pp_pctl']], on='playerId', how='left')
    result = result.merge(pk[['playerId', 'pk_pctl']], on='playerId', how='left')

    season_totals = df[df['situation'] == 'all'].copy()
    season_totals['season_goals'] = season_totals['I_F_goals']
    season_totals['season_assists'] = season_totals['I_F_primaryAssists'] + season_totals['I_F_secondaryAssists']
    season_totals['season_points'] = season_totals['season_goals'] + season_totals['season_assists']
    season_totals['pim'] = season_totals['I_F_penalityMinutes']
    season_totals['avg_toi_min'] = season_totals['icetime'] / season_totals['games_played'] / 60
    result = result.merge(
        season_totals[['playerId', 'season_goals', 'season_assists', 'season_points', 'pim', 'avg_toi_min']],
        on='playerId', how='left'
    )
    return result


@st.cache_data(ttl=3600)
def build_goalie_percentiles(csv_path, min_gp=10):
    goalies_df = fetch_csv(csv_path)
    goalies_df = goalies_df[goalies_df['games_played'] >= min_gp]

    ev_goalies = goalies_df[goalies_df['situation'] == '5on5'].copy()
    ev_goalies = ev_goalies[ev_goalies['icetime'] >= 600].copy()

    ev_goalies['gsax_raw'] = ev_goalies['xGoals'] - ev_goalies['goals']
    ev_goalies['gsax_per60'] = ev_goalies['gsax_raw'] / ev_goalies['icetime'] * 3600
    ev_goalies['ev_gsax_pctl'] = ev_goalies['gsax_per60'].rank(pct=True) * 100

    ev_goalies['hd_gsax_raw'] = ev_goalies['highDangerxGoals'] - ev_goalies['highDangerGoals']
    ev_goalies['hd_gsax_per60'] = ev_goalies['hd_gsax_raw'] / ev_goalies['icetime'] * 3600
    ev_goalies['high_danger_pctl'] = ev_goalies['hd_gsax_per60'].rank(pct=True) * 100

    ev_goalies['rebound_raw'] = ev_goalies['xRebounds'] - ev_goalies['rebounds']
    ev_goalies['rebound_per60'] = ev_goalies['rebound_raw'] / ev_goalies['icetime'] * 3600
    ev_goalies['rebound_pctl'] = ev_goalies['rebound_per60'].rank(pct=True) * 100

    pk_goalies = goalies_df[goalies_df['situation'] == '4on5'].copy()
    pk_goalies = pk_goalies[pk_goalies['icetime'] >= 60].copy()
    pk_goalies['pk_gsax_raw'] = pk_goalies['xGoals'] - pk_goalies['goals']
    pk_goalies['pk_gsax_per60'] = pk_goalies['pk_gsax_raw'] / pk_goalies['icetime'] * 3600
    pk_goalies['pk_gsax_pctl'] = pk_goalies['pk_gsax_per60'].rank(pct=True) * 100

    result = ev_goalies[['playerId', 'name', 'team', 'games_played',
                          'ev_gsax_pctl', 'high_danger_pctl', 'rebound_pctl']].copy()
    result = result.merge(pk_goalies[['playerId', 'pk_gsax_pctl']], on='playerId', how='left')

    season_totals = goalies_df[goalies_df['situation'] == 'all'].copy()
    season_totals['save_pct'] = 1 - (season_totals['goals'] / season_totals['ongoal'])
    season_totals['gaa'] = season_totals['goals'] / season_totals['icetime'] * 3600
    result = result.merge(
        season_totals[['playerId', 'save_pct', 'gaa']], on='playerId', how='left'
    )
    return result


def find_players(name, skater_league, goalie_league):
    skater_matches = skater_league[skater_league['name'].str.contains(name, case=False, na=False)]
    goalie_matches = goalie_league[goalie_league['name'].str.contains(name, case=False, na=False)]
    return skater_matches, goalie_matches


def get_player_card(name, skater_league, goalie_league):
    skater_match = skater_league[skater_league['name'] == name]
    goalie_match = goalie_league[goalie_league['name'] == name]
    if not skater_match.empty:
        return "skater", skater_match.iloc[0]
    elif not goalie_match.empty:
        return "goalie", goalie_match.iloc[0]
    else:
        return None, None


SKATER_LABELS = {
    "ev_offence_pctl": "EV Offence", "ev_defence_pctl": "EV Defence",
    "pp_pctl": "PP", "pk_pctl": "PK", "finishing_pctl": "Finishing",
    "goals_pctl": "Goals", "a1_pctl": "1st Assists", "penalties_pctl": "Penalties",
}

GOALIE_LABELS = {
    "ev_gsax_pctl": "EV GSAx", "high_danger_pctl": "High Danger",
    "rebound_pctl": "Rebound Control", "pk_gsax_pctl": "PK GSAx",
}


def plot_player_card(row, stat_labels):
    stats = list(stat_labels.keys())
    labels = list(stat_labels.values())
    values = [row.get(s, None) for s in stats]

    fig, ax = plt.subplots(figsize=(7, 4.5))

    colors = []
    for v in values:
        if v is None or pd.isna(v):
            colors.append("#cccccc")
        else:
            t = v / 100
            colors.append((1 - t, t, 0.0))

    display_values = [0 if (v is None or pd.isna(v)) else v for v in values]
    bars = ax.barh(labels, display_values, color=colors)

    for bar, v in zip(bars, values):
        label = "NA" if (v is None or pd.isna(v)) else f"{v:.0f}%"
        ax.text(max(bar.get_width() + 2, 4), bar.get_y() + bar.get_height() / 2,
                 label, va="center", fontsize=10)

    ax.set_xlim(0, 110)
    ax.invert_yaxis()
    ax.set_title(f"{row['name']} -- Percentile Rankings")
    ax.set_xlabel("Percentile vs. peers")
    plt.tight_layout()
    return fig


def render_player_card(kind, row):
    if kind == "skater":
        st.subheader(f"{row['name']} ({row['position']}, {row['team']}) -- {SEASON_LABEL} Skater")
    else:
        st.subheader(f"{row['name']} (G, {row['team']}) -- {SEASON_LABEL} Goalie")

    if kind == "skater":
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Games Played", int(row['games_played']))
        col2.metric("Goals", int(row['season_goals']))
        col3.metric("Assists", int(row['season_assists']))
        col4.metric("Points", int(row['season_points']))
        col5.metric("PIM", int(row['pim']))
        col6.metric("Avg TOI", f"{row['avg_toi_min']:.1f} min")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Games Played", int(row['games_played']))
        col2.metric("Save %", f"{row['save_pct']:.3f}")
        col3.metric("GAA", f"{row['gaa']:.2f}")

    labels = SKATER_LABELS if kind == "skater" else GOALIE_LABELS
    fig = plot_player_card(row, labels)
    st.pyplot(fig)

    render_three_year_trend(kind, row['name'])


TREND_STATS = {
    "skater": [
        ("ev_offence_pctl", "EV Offence", "#4a9de0"),
        ("ev_defence_pctl", "EV Defence", "#d64550"),
        ("finishing_pctl", "Finishing", "#f2f2f2"),
    ],
    "goalie": [
        ("ev_gsax_pctl", "EV GSAx", "#4a9de0"),
        ("high_danger_pctl", "High Danger", "#d64550"),
        ("rebound_pctl", "Rebound Control", "#f2f2f2"),
    ],
}


def get_recent_seasons_history(name, kind, start_year, num_seasons=3, max_lookback=8):
    history = []
    year = start_year
    attempts = 0
    while len(history) < num_seasons and attempts < max_lookback and year >= EARLIEST_SEASON_START_YEAR:
        season_label = f"{year}-{str(year + 1)[-2:]}"
        try:
            if kind == "skater":
                url = f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/regular/skaters.csv"
                league = build_percentiles(url)
            else:
                url = f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/regular/goalies.csv"
                league = build_goalie_percentiles(url)
            match = league[league["name"] == name]
            if not match.empty:
                history.append((season_label, match.iloc[0]))
        except Exception:
            pass
        year -= 1
        attempts += 1
    history.reverse()
    return history


def plot_trend_chart(history, kind):
    fig, ax = plt.subplots(figsize=(7, 4))
    seasons = [season for season, _ in history]

    for key, label, color in TREND_STATS[kind]:
        values = [row.get(key, None) for _, row in history]
        ax.plot(seasons, values, marker="o", label=label, color=color)

    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentile")
    ax.set_title("3-Season Trend")
    ax.legend()
    plt.tight_layout()
    return fig


def render_three_year_trend(kind, name):
    history = get_recent_seasons_history(name, kind, selected_start_year)
    if len(history) == 0:
        st.caption("No prior-season data available for this player yet.")
        return
    fig = plot_trend_chart(history, kind)
    st.pyplot(fig)


# ---------------------------------------------------------------------
# The Streamlit interface.
# ---------------------------------------------------------------------

st.title("Hockeydex")
st.caption("by [bennett2lin](https://github.com/bennett2lin) -- Source: MoneyPuck")

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.1rem; }
[data-testid="stMetricLabel"] { font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

with st.expander("What do these stats mean? (click to expand)"):
    st.markdown("""
**All percentile boxes are ranked against other players in the same role** (forwards vs.
forwards, defensemen vs. defensemen, goalies vs. goalies) with a minimum games-played
cutoff applied, so a 50th percentile always means "middle of the pack for this role,"
not "average across the whole league."

#### Skater stats

- **EV Offence** -- Individual scoring rate (goals + assists) at 5-on-5, per 60 minutes.
- **EV Defence** -- How many expected goals were allowed while this player was on the ice
  at 5-on-5 (fewer is better). Team-level, not solely this player's fault.
- **PP** -- Power-play scoring rate, same idea as EV Offence but isolated to the man advantage.
- **PK** -- Penalty-kill defensive rate, same idea as EV Defence but isolated to shorthanded play.
- **Finishing** -- Goals actually scored vs. expected goals from this player's own shots.
  A high number means outscoring their shot quality (elite shooting, or possibly a hot
  streak that won't fully repeat -- shooting stats are less consistent year to year than
  most others here).
- **Goals / 1st Assists** -- Straightforward scoring-rate stats.
- **Penalties** -- Net penalty differential (drawn minus taken) per 60 minutes.

**Not included:** Competition and Teammates (how tough their opponents/linemates are) --
these require play-by-play regression modeling (RAPM), not just season totals, so they're
left out rather than faked.

#### Goalie stats

- **EV GSAx** -- Goals Saved above Expected at 5-on-5: actual goals allowed vs. what an
  average goalie would allow facing the same shots. Positive is good.
- **High Danger** -- Same GSAx idea, but isolated to just the toughest, highest-quality
  scoring chances.
- **Rebound Control** -- Expected rebounds allowed minus actual rebounds allowed. Fewer
  rebounds than expected is good puck control.
- **PK GSAx** -- Same GSAx idea, isolated to the penalty kill.

**Not included:** Quality Start %, Really Good/Bad Start %, and year-over-year Consistency --
these need individual game-by-game logs, not season totals, so they're left out.
""")

MOST_RECENT_SEASON_START_YEAR = 2025
EARLIEST_SEASON_START_YEAR = 2008

season_start_years = list(range(MOST_RECENT_SEASON_START_YEAR, EARLIEST_SEASON_START_YEAR - 1, -1))
season_labels = [f"{y}-{str(y + 1)[-2:]}" for y in season_start_years]

query_params = st.query_params
linked_player = query_params.get("player")
linked_season = query_params.get("season")

default_season_index = 0
if linked_season in season_labels:
    default_season_index = season_labels.index(linked_season)

SEASON_LABEL = st.selectbox("Season:", season_labels, index=default_season_index)
selected_start_year = int(SEASON_LABEL.split("-")[0])

SKATERS_URL = f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{selected_start_year}/regular/skaters.csv"
GOALIES_URL = f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{selected_start_year}/regular/goalies.csv"

try:
    skater_league = build_percentiles(SKATERS_URL)
    goalie_league = build_goalie_percentiles(GOALIES_URL)
except Exception as e:
    st.error(
        f"Couldn't load {SEASON_LABEL} data from MoneyPuck. This usually means that "
        f"season hasn't started yet (if you picked the most recent one), or MoneyPuck "
        f"hasn't published this file. Try a different, already-completed season from "
        f"the dropdown above.\n\nDetails: {e}"
    )
    st.stop()

name = st.text_input("Search a player name:", placeholder="e.g. Celebrini, or just Mac")

chosen_name = None
if name:
    skater_matches, goalie_matches = find_players(name, skater_league, goalie_league)
    all_names = list(skater_matches['name']) + list(goalie_matches['name'])

    if len(all_names) == 0:
        st.error(f"No qualifying player found matching '{name}'. Check spelling, or they may not meet the minimum games-played cutoff.")
    elif len(all_names) == 1:
        chosen_name = all_names[0]
    else:
        chosen_name = st.selectbox("Multiple matches found -- pick one:", all_names)
elif linked_player:
    chosen_name = linked_player

if chosen_name:
    kind, row = get_player_card(chosen_name, skater_league, goalie_league)
    if row is not None:
        render_player_card(kind, row)

SKATER_LEADERBOARD_COLUMNS = {
    "games_played": "GP", "season_goals": "Goals", "season_assists": "Assists",
    "season_points": "Points", "pim": "PIM", "avg_toi_min": "Avg TOI",
    "ev_offence_pctl": "EV Offence %ile", "ev_defence_pctl": "EV Defence %ile",
    "pp_pctl": "PP %ile", "pk_pctl": "PK %ile", "finishing_pctl": "Finishing %ile",
    "penalties_pctl": "Penalties %ile",
}

GOALIE_LEADERBOARD_COLUMNS = {
    "games_played": "GP", "save_pct": "Save %", "gaa": "GAA",
    "ev_gsax_pctl": "EV GSAx %ile", "high_danger_pctl": "High Danger %ile",
    "rebound_pctl": "Rebound Control %ile", "pk_gsax_pctl": "PK GSAx %ile",
}

st.header("Leaderboard")

leaderboard_kind = st.radio("Show:", ["Skaters", "Goalies"], horizontal=True)

if leaderboard_kind == "Skaters":
    columns_map = SKATER_LEADERBOARD_COLUMNS
    source_league = skater_league

    position_filter = st.selectbox("Filter by position:", ["All", "C", "L", "R", "D"])
    if position_filter != "All":
        source_league = source_league[source_league["position"] == position_filter]

    leaderboard = source_league[["name", "position", "team"] + list(columns_map.keys())].copy()
else:
    columns_map = GOALIE_LEADERBOARD_COLUMNS
    source_league = goalie_league
    leaderboard = source_league[["name", "team"] + list(columns_map.keys())].copy()

leaderboard["name"] = leaderboard["name"].apply(
    lambda n: f"?player={n}&season={SEASON_LABEL}"
)

rename_map = {"name": "Name", "team": "Team", "position": "Pos", **columns_map}
leaderboard = leaderboard.rename(columns=rename_map)
leaderboard = leaderboard.round(3)

st.dataframe(
    leaderboard,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Name": st.column_config.LinkColumn("Name", display_text=r"player=([^&]*)"),
    },
)
