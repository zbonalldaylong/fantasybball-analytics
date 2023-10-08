import requests
from bs4 import BeautifulSoup as bs
import regex as re
import pandas as pd
import time
from os.path import exists


class CBS:
    def __init__(self):
        self.login_info = {
            "userid": "zfillingham@gmail.com",
            "password": "roflrofl",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
        }

        self.tracked_datapoints = [
            "team_name",
            "manager",
            "team_id",
            "team_url",
            "record",
            "logo_url",
            "weekly_games",
            "total_salary",
        ]
        self.tracked_statcats = [
            "player_name",
            "salary",
            "contract",
            "position",
            "g",
            "mpg",
            "fg",
            "fgp",
            "fgpg",
            "ft",
            "ftp",
            "ftpg",
            "3pt",
            "3ptp",
            "3ptpg",
            "rpg",
            "apg",
            "spg",
            "tpg",
            "bpg",
            "ppg",
            "cbs_rank",
        ]
        self.tracked_zcats = [
            "player_name",
            "g",
            "fgpg",
            "fgp",
            "ftpg",
            "ftp",
            "3ptpg",
            "rpg",
            "apg",
            "spg",
            "tpg",
            "bpg",
            "ppg",
            "zrank",
            "team_id",
        ]

        # URLS
        self.login_url = "https://www.cbssports.com/login?"
        self.league_home = (
            "https://forkeeps.basketball.cbssports.com/?tid=1696446175&login=confirmed"
        )
        self.league_standings = (
            "https://forkeeps.basketball.cbssports.com/standings/overall"
        )
        self.league_allplayers_cy = "https://forkeeps.basketball.cbssports.com/stats/stats-main/all:C:G:F/ytd:p/standard/projections?print_rows=9999"
        self.league_2022 = "https://forkeeps.basketball.cbssports.com/stats/stats-main/all:C:G:F/2022:p/standard/stats?print_rows=9999"

        # HTML FILES
        self.souped_league_home = bs(
            open("league_home.html", mode="r", encoding="utf-8"), "html.parser"
        )
        self.souped_league_standings = bs(
            open("league_standings.html", mode="r", encoding="utf-8"), "html.parser"
        )
        self.souped_allplayers = bs(
            open("html/all_players.html", mode="r", encoding="utf-8"), "html.parser"
        )

        # DF FILES
        if exists("pickle/pickled_league_df.pkl"):
            self.league_df = pd.read_pickle("pickle/pickled_league_df.pkl")
        else:
            self.league_df = self._league_builder()

        if exists("pickle/pickled_roster_df.pkl"):
            self.roster_current = pd.read_pickle("pickle/pickled_roster_df.pkl")
        else:
            self.roster_current = self._roster_builder("html/all_players.html")

        if exists("pickle/pickled_roster_2022.pkl"):
            self.roster_2022 = pd.read_pickle("pickle/pickled_roster_2022.pkl")
        else:
            self._roster_builder("html/roster_2022.html").drop(
                columns=["salary", "position", "contract"]
            )

    # Updates local html files so as not to hammer their website with requests
    def update(self):

        # UPDATE HTML FILES
        with requests.Session() as s:
            s.post(self.login_url, data=self.login_info)

            # League home
            league_home_rawhtml = s.get(self.league_home)
            league_home_rawhtml.encoding = "utf-8"
            souped_league_home = bs(league_home_rawhtml.text, "html.parser")
            with open("league_home.html", "w", encoding="utf-8") as file:
                file.write(str(souped_league_home))

            time.sleep(1)

            # League standings
            league_standings_rawhtml = s.get(self.league_standings)
            league_standings_rawhtml.encoding = "utf-8"
            souped_league_standings = bs(league_standings_rawhtml.text, "html.parser")
            with open("league_standings.html", "w", encoding="utf-8") as file:
                file.write(str(souped_league_standings))

            time.sleep(1)

            team_1_html = s.get("https://forkeeps.basketball.cbssports.com/teams/1")
            team_1_html.encoding = "utf-8"
            souped_team_1 = bs(team_1_html.text, "html.parser")
            with open("html/team_1.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_1))

            time.sleep(1)

            team_2_html = s.get("https://forkeeps.basketball.cbssports.com/teams/2")
            team_2_html.encoding = "utf-8"
            souped_team_2 = bs(team_2_html.text, "html.parser")
            with open("html/team_2.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_2))

            time.sleep(1)

            team_3_html = s.get("https://forkeeps.basketball.cbssports.com/teams/3")
            team_3_html.encoding = "utf-8"
            souped_team_3 = bs(team_3_html.text, "html.parser")
            with open("html/team_3.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_3))

            time.sleep(1)

            team_4_html = s.get("https://forkeeps.basketball.cbssports.com/teams/4")
            team_4_html.encoding = "utf-8"
            souped_team_4 = bs(team_4_html.text, "html.parser")
            with open("html/team_4.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_4))

            time.sleep(1)

            team_5_html = s.get("https://forkeeps.basketball.cbssports.com/teams/5")
            team_5_html.encoding = "utf-8"
            souped_team_5 = bs(team_5_html.text, "html.parser")
            with open("html/team_5.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_5))

            time.sleep(1)

            team_6_html = s.get("https://forkeeps.basketball.cbssports.com/teams/6")
            team_6_html.encoding = "utf-8"
            souped_team_6 = bs(team_6_html.text, "html.parser")
            with open("html/team_6.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_6))

            time.sleep(1)

            team_7_html = s.get("https://forkeeps.basketball.cbssports.com/teams/7")
            team_7_html.encoding = "utf-8"
            souped_team_7 = bs(team_7_html.text, "html.parser")
            with open("html/team_7.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_7))

            time.sleep(1)

            team_8_html = s.get("https://forkeeps.basketball.cbssports.com/teams/8")
            team_8_html.encoding = "utf-8"
            souped_team_8 = bs(team_8_html.text, "html.parser")
            with open("html/team_8.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_8))

            time.sleep(1)

            team_9_html = s.get("https://forkeeps.basketball.cbssports.com/teams/9")
            team_9_html.encoding = "utf-8"
            souped_team_9 = bs(team_9_html.text, "html.parser")
            with open("html/team_9.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_9))

            time.sleep(1)

            team_10_html = s.get("https://forkeeps.basketball.cbssports.com/teams/10")
            team_10_html.encoding = "utf-8"
            souped_team_10 = bs(team_10_html.text, "html.parser")
            with open("html/team_10.html", "w", encoding="utf-8") as file:
                file.write(str(souped_team_10))

            time.sleep(1)

            all_players_html = s.get(self.league_allplayers_cy)
            all_players_html.encoding = "utf-8"
            souped_all_players = bs(all_players_html.text, "html.parser")
            with open("html/all_players.html", "w", encoding="utf-8") as file:
                file.write(str(souped_all_players))

            time.sleep(1)

            roster_2022_html = s.get(self.league_2022)
            roster_2022_html.encoding = "utf-8"
            souped_roster_2022 = bs(roster_2022_html.text, "html.parser")
            with open("html/roster_2022.html", "w", encoding="utf-8") as file:
                file.write(str(souped_roster_2022))

        # UPDATE DF PICKLES
        pickled_league_df = self._league_builder()
        pickled_roster_df = self._roster_builder("html/all_players.html")
        pickled_roster_2022 = self._roster_builder("html/roster_2022.html").drop(
            columns=["salary", "position", "contract"]
        )

        pickled_league_df, pickled_roster_df = self._additional_roster_filler(
            pickled_league_df, pickled_roster_df
        )

        pickled_league_df.to_pickle("pickle/pickled_league_df.pkl")
        pickled_roster_df.to_pickle("pickle/pickled_roster_df.pkl")
        pickled_roster_2022.to_pickle("pickle/pickled_roster_2022.pkl")

    def session(self):
        with requests.Session() as s:
            s.post(self.login_url, data=self.login_info)
            return s

    # Builds the basic league info df on initialization
    def _league_builder(self):
        teams_exclusion_list = []
        df_output = pd.DataFrame(columns=self.tracked_datapoints)

        ls_split_html = str(self.souped_league_standings).split("FantasyGlobalChatJson")
        teams_chunk = re.findall(
            r'(?<="team" : {)[\s\S]*?(?=},)', "".join(ls_split_html[1].split("attrib"))
        )

        for x in teams_chunk:
            # Team name
            team_name = (
                re.search(r'(?<="name" : ").*?(?=")', x).group(0).replace("'", "")
            )
            if team_name not in teams_exclusion_list:
                teams_exclusion_list.append(team_name)
            else:
                continue
            team_manager = (
                re.search(r'(?<="long_abbr" : ").*?(?=")', x).group(0).replace("'", "")
            )
            team_logo = (
                re.search(r'(?<="logo" : ").*?(?=")', x).group(0).replace("'", "")
            )
            team_id = re.search(r'(?<="id" : ").*?(?=")', x).group(0)
            team_url = str(f"https://forkeeps.basketball.cbssports.com/teams/{team_id}")
            new_entry = pd.DataFrame.from_dict(
                {
                    "manager": [team_manager],
                    "team_id": team_id,
                    "team_url": team_url,
                    "logo_url": [team_logo],
                }
            )
            df_output = pd.concat([df_output, new_entry])

        # NEXT: Go to league home and get the records based on the team_id in the code.
        lh_html = self.souped_league_home
        standings = lh_html.find("div", {"id": "hpfcLeagueStandings"})

        for x in str(standings).split("\n"):
            if "href" in x:
                # Team record
                try:
                    t_id = re.search(r'(?<=<a href="/teams/).*?(?=")', x).group(0)
                    t_record = re.search(
                        r'(?<=<td align="right">).*?(?=</td>)', x
                    ).group(0)
                    df_output["record"][df_output.team_id == t_id] = t_record
                except:
                    pass

                # Team name
                if 'span class="tooltip"' in x:
                    team_name = re.search(
                        r'(?<=class="tooltip" title=").*?(?=">)', x
                    ).group(0)
                    df_output["team_name"][df_output.team_id == t_id] = team_name
                    continue
                else:
                    pass
                try:
                    regex_string = str(fr'(?<=<a href="/teams/{t_id}">).*?(?=</a>)')
                    team_name = re.search(regex_string, x).group(0)
                    df_output["team_name"][df_output.team_id == t_id] = team_name
                except:
                    pass

        df_output.set_index(["team_name"], inplace=True)
        return df_output

    # Builds the roster (can be used for past/present years)
    def _roster_builder(self, html):

        df_output = pd.DataFrame(columns=self.tracked_statcats)

        with open(html, "r", encoding="utf-8") as f:
            souped_allplayers = bs(f, "html.parser")

        raw_allplayers = souped_allplayers.find("div", {"id": "sortableStats"})

        for x in str(raw_allplayers).split("\n"):

            # Players on teams
            if "/teams/" in x:
                player_name = re.search(
                    r'(?<=playerpage/\d{4,9}.*">)(.*?)(?=</a>)', x
                ).group(0)
                team_id = int(
                    re.search(r'(?<=<a href="/teams/)(.*?)(?=">)', x).group(0)
                )

                raw_stats = re.search(
                    r'(?<=<td align="right")([\s\S]*?)(?=</tr>)', x
                ).group(0)
                stats_list = re.findall(r"(?<=>)([0-9.]+)(?=<)", raw_stats)

                new_entry = pd.DataFrame.from_dict(
                    {
                        "player_name": [player_name],
                        "team_id": [team_id],
                        "salary": [8],
                        "contract": ["B"],
                        "g": [stats_list[0]],
                        "mpg": [stats_list[1]],
                        "fg": [stats_list[2]],
                        "fgp": [stats_list[3]],
                        "ft": [stats_list[4]],
                        "ftp": [stats_list[5]],
                        "3pt": [stats_list[6]],
                        "3ptp": [stats_list[7]],
                        "rpg": [stats_list[8]],
                        "apg": [stats_list[9]],
                        "spg": [stats_list[10]],
                        "tpg": [stats_list[11]],
                        "bpg": [stats_list[12]],
                        "ppg": [stats_list[13]],
                        "cbs_rank": [stats_list[14]],
                    }
                )
                df_output = pd.concat([df_output, new_entry])

            # Free agents
            else:
                team_id = 0
                try:
                    player_name = re.search(
                        r'(?<=playerpage/\d{4,9}.*">)(.*?)(?=</a>)', x
                    ).group(0)
                    raw_stats = re.search(
                        r'(?<=<td align="right")([\s\S]*?)(?=</tr>)', x
                    ).group(0)
                    stats_list = re.findall(r"(?<=>)([0-9.]+)(?=<)", raw_stats)
                    new_entry = pd.DataFrame.from_dict(
                        {
                            "player_name": [player_name],
                            "team_id": [team_id],
                            "salary": [8],
                            "contract": ["B"],
                            "g": [stats_list[0]],
                            "mpg": [stats_list[1]],
                            "fg": [stats_list[2]],
                            "fgp": [stats_list[3]],
                            "ft": [stats_list[4]],
                            "ftp": [stats_list[5]],
                            "3pt": [stats_list[6]],
                            "3ptp": [stats_list[7]],
                            "rpg": [stats_list[8]],
                            "apg": [stats_list[9]],
                            "spg": [stats_list[10]],
                            "tpg": [stats_list[11]],
                            "bpg": [stats_list[12]],
                            "ppg": [stats_list[13]],
                            "cbs_rank": [stats_list[14]],
                        }
                    )
                    df_output = pd.concat([df_output, new_entry])
                except:
                    pass

        # Data and formatting
        df_output = df_output.astype(
            {
                "salary": int,
                "g": float,
                "mpg": float,
                "fg": float,
                "fgp": float,
                "ft": float,
                "ftp": float,
                "3pt": float,
                "3ptp": float,
                "rpg": float,
                "apg": float,
                "spg": float,
                "tpg": float,
                "bpg": float,
                "ppg": float,
                "cbs_rank": int,
                "team_id": int,
            }
        )

        # Pare the roster to save CPU time and allow for more accurate z scores
        condition_1 = df_output["cbs_rank"] <= 300
        condition_2 = df_output["team_id"] >= 1
        df_output = df_output[condition_1 | condition_2]

        # Add useful data columns
        df_output["fgpg"] = df_output.apply(
            lambda row: row.fg / row.g if row.g > 0 else 0, axis=1
        ).round(2)
        df_output["ftpg"] = df_output.apply(
            lambda row: row.ft / row.g if row.g > 0 else 0, axis=1
        ).round(2)
        df_output["3ptpg"] = df_output.apply(
            lambda row: row["3pt"] / row.g if row.g > 0 else 0, axis=1
        ).round(2)

        # Set the index to player name
        df_output.set_index("player_name", inplace=True)

        return df_output

    # Fills in the rest of the data from team pages: player salary, position, total weekly games
    def _additional_roster_filler(self, league, roster):

        # Goes through all the teams
        for id in range(1, 11):

            with open(f"html/team_{id}.html", "r", encoding="utf-8") as f:
                souped_team = bs(f, "html.parser")

            # Harvest data
            raw_lineup = souped_team.find("div", {"id": "lineup_views"})
            salary_list = []
            games_list = []
            weekly_game_counter = 0

            player_names = re.findall(
                r'(?<=aria-label=" ).*?(?= " class="playerLink")', str(raw_lineup)
            )
            positions = re.findall(r"(?<=\s)[FGC,]+(?=\s|\s)", raw_lineup.text)
            # total_salary = re.search(r'(?<=Total Salary: ).*?(?=</td>)', str(raw_lineup)).group(0).strip()

            for x in str(raw_lineup).split("\n"):
                try:
                    salary_cost = re.search(
                        r'<td align="right">(\d+)<\/td><td align="right">([A-Z])<\/td>',
                        x,
                    ).group(1)
                    salary_type = re.search(
                        r'<td align="right">(\d+)<\/td><td align="right">([A-Z])<\/td>',
                        x,
                    ).group(2)
                    player_salary = (salary_cost, salary_type)
                    salary_list.append(player_salary)
                except:
                    pass
                try:
                    weekly_game_counter += int(
                        re.search(r"(?:Home: )(\d+)", x).group(1)
                    ) + int(re.search(r"(?:Away: )(\d+)", x).group(1))
                except:
                    pass

            # Record data on league df
            league["weekly_games"][league.team_id == str(id)] = weekly_game_counter
            league["total_salary"][league.team_id == str(id)] = sum(
                [int(x[0]) for x in salary_list]
            )

            # Record data on roster df
            for name, sal, pos in zip(player_names, salary_list, positions):
                roster["salary"][roster.index == str(name)] = int(sal[0])
                roster["contract"][roster.index == str(name)] = sal[1]
                roster["position"][roster.index == str(name)] = pos.replace(",", "")

        return league, roster

    # Outputs a df roster of zscores
    def _zroster_builder(self, roster):
        exclusions = ["player_name", "g", "team_id", "zrank"]
        data_refs = {
            str(x + "-avg"): None for x in self.tracked_zcats if x not in exclusions
        } | {str(x + "-stdev"): None for x in self.tracked_zcats if x not in exclusions}

        for x in self.tracked_zcats:
            if x not in exclusions:
                data_refs.update({str(x + "-avg"): roster[x].mean().round(3)})
                data_refs.update({str(x + "-stdev"): roster[x].std().round(3)})

        roster["fg-impact"] = roster.apply(
            lambda row: (row.fgp - data_refs.get("fgp-avg")) * row.fgpg, axis=1
        ).round(3)
        roster["ft-impact"] = roster.apply(
            lambda row: (row.ftp - data_refs.get("ftp-avg")) * row.ftpg, axis=1
        ).round(3)

        data_refs["fg-impact-stdev"] = roster["fg-impact"].std().round(3)
        data_refs["ft-impact-stdev"] = roster["ft-impact"].std().round(3)

        data_refs["fg-impact-avg"] = roster["fg-impact"].mean().round(3)
        data_refs["ft-impact-avg"] = roster["ft-impact"].mean().round(3)

        # Build the z-roster
        z_df = pd.DataFrame(columns=self.tracked_zcats)

        for index, row in roster.iterrows():
            new_entry = {
                "player_name": [index],
                "g": [row["g"]],
                "fgpg": [
                    round(
                        (
                            ((row["fgp"] - data_refs["fgp-avg"]) * row["fgpg"])
                            - data_refs["fg-impact-avg"]
                        )
                        / data_refs["fg-impact-stdev"],
                        3,
                    )
                ],
                "ftpg": [
                    round(
                        (
                            ((row["ftp"] - data_refs["ftp-avg"]) * row["ftpg"])
                            - data_refs["ft-impact-avg"]
                        )
                        / data_refs["ft-impact-stdev"],
                        3,
                    )
                ],
                "3ptpg": [
                    round(
                        (row["3ptpg"] - data_refs["3ptpg-avg"])
                        / data_refs["3ptpg-stdev"],
                        3,
                    )
                ],
                "rpg": [
                    round(
                        (row["rpg"] - data_refs["rpg-avg"]) / data_refs["rpg-stdev"], 3
                    )
                ],
                "apg": [
                    round(
                        (row["apg"] - data_refs["apg-avg"]) / data_refs["apg-stdev"], 3
                    )
                ],
                "spg": [
                    round(
                        (row["spg"] - data_refs["spg-avg"]) / data_refs["spg-stdev"], 3
                    )
                ],
                "tpg": [
                    round(
                        ((row["tpg"] - data_refs["tpg-avg"]) / data_refs["tpg-stdev"])
                        * -1,
                        3,
                    )
                ],
                "bpg": [
                    round(
                        (row["bpg"] - data_refs["bpg-avg"]) / data_refs["bpg-stdev"], 3
                    )
                ],
                "ppg": [
                    round(
                        (row["ppg"] - data_refs["ppg-avg"]) / data_refs["ppg-stdev"], 3
                    )
                ],
                "team_id": [int(row["team_id"])],
            }

            z_df = pd.concat([pd.DataFrame.from_dict(new_entry), z_df])

        # self.tracked_zcats = ['player_name', 'g', 'fgpg', 'fgp', 'ftpg', 'ftp', '3ptpg', 'rpg', 'apg', 'spg', 'tpg', 'bpg', 'ppg', 'zrank', 'team_id']

        print(z_df)
        return z_df


if __name__ == "__main__":

    pd.set_option("mode.chained_assignment", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", None)

    cbs = CBS()

    cbs._zroster_builder(cbs.roster_2022)
