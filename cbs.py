import regex as re
import os
from os.path import exists
import sys
import time
import requests
import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup as bs

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class CBS:
    def __init__(self, cbs_user: str, cbs_pass: str, c_path: str):

        # Logging (output to file)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        log_path = Path(__file__).parent / "logs/commentscrape.log"
        self.file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="w")
        self.file_format = logging.Formatter(
            "%(asctime)s, %(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
        )
        self.file_handler.setFormatter(self.file_format)
        self.logger.addHandler(self.file_handler)

        with open(c_path, "r") as f:
            json_config = json.load(f)

        self.config = json_config
        self.config["login_info"].update({"userid": cbs_user, "password": cbs_pass})
        self.punts = ["3pt", "ppg"]
        self.config["league_total_budget"] = 2000
        self.c_path = c_path

        # LOAD FROM HTML FILES
        if exists(Path(__file__).parent / "html/league_home.html"):
            path = Path(__file__).parent / "html/league_home.html"
            with path.open("r", encoding="utf-8") as f:
                self.souped_league_home = bs(f, "html.parser")
        else:
            self.update()

        if exists(Path(__file__).parent / "html/league_standings.html"):
            path = Path(__file__).parent / "html/league_standings.html"
            with path.open("r", encoding="utf-8") as f:
                self.souped_league_standings = bs(f, "html.parser")
        else:
            self.update()

        if exists(Path(__file__).parent / "html/all_players.html"):
            path = Path(__file__).parent / "html/all_players.html"
            with path.open("r", encoding="utf-8") as f:
                self.souped_allplayers = bs(f, "html.parser")
        else:
            self.update()

        # LOAD FROM DF FILES
        if exists(Path(__file__).parent / "pickle/pickled_league_df.pkl"):
            self.league_df = pd.read_pickle(
                Path(__file__).parent / "pickle/pickled_league_df.pkl"
            )
        else:
            self.update()

        if exists(Path(__file__).parent / "pickle/pickled_roster_df.pkl"):
            self.roster_current = pd.read_pickle(
                Path(__file__).parent / "pickle/pickled_roster_df.pkl"
            )
        else:
            self.update()

        if exists(Path(__file__).parent / "pickle/pickled_roster_2022.pkl"):
            self.roster_2022 = pd.read_pickle(
                Path(__file__).parent / "pickle/pickled_roster_2022.pkl"
            )
        else:
            self.update()

        if exists(Path(__file__).parent / "pickle/pickled_zscores.pkl"):
            self.zscores = pd.read_pickle(
                Path(__file__).parent / "pickle/pickled_zscores.pkl"
            )
        else:
            self.update()

        if exists(Path(__file__).parent / "pickle/pickled_record.pkl"):
            self.league_record = pd.read_pickle(
                Path(__file__).parent / "pickle/pickled_record.pkl"
            )
        else:
            self.update()

    # Updates local html files so as not to hammer their website with requests
    def update(self, refresh=False):
        def _html_updater():
            # UPDATE HTML FILES
            with requests.Session() as s:
                s.post(self.config["login_url"], data=self.config["login_info"])

                # League home
                league_home_rawhtml = s.get(self.config["league_home"])
                league_home_rawhtml.encoding = "utf-8"
                souped_league_home = bs(league_home_rawhtml.text, "html.parser")
                html_path = Path(__file__).parent / "html/league_home.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_league_home))

                # League standings
                league_standings_rawhtml = s.get(self.config["league_standings"])
                league_standings_rawhtml.encoding = "utf-8"
                souped_league_standings = bs(
                    league_standings_rawhtml.text, "html.parser"
                )
                html_path = Path(__file__).parent / "html/league_standings.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_league_standings))

                team_1_html = s.get("https://forkeeps.basketball.cbssports.com/teams/1")
                team_1_html.encoding = "utf-8"
                souped_team_1 = bs(team_1_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_1.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_1))

                team_2_html = s.get("https://forkeeps.basketball.cbssports.com/teams/2")
                team_2_html.encoding = "utf-8"
                souped_team_2 = bs(team_2_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_2.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_2))

                team_3_html = s.get("https://forkeeps.basketball.cbssports.com/teams/3")
                team_3_html.encoding = "utf-8"
                souped_team_3 = bs(team_3_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_3.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_3))

                team_4_html = s.get("https://forkeeps.basketball.cbssports.com/teams/4")
                team_4_html.encoding = "utf-8"
                souped_team_4 = bs(team_4_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_4.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_4))

                team_5_html = s.get("https://forkeeps.basketball.cbssports.com/teams/5")
                team_5_html.encoding = "utf-8"
                souped_team_5 = bs(team_5_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_5.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_5))

                team_6_html = s.get("https://forkeeps.basketball.cbssports.com/teams/6")
                team_6_html.encoding = "utf-8"
                souped_team_6 = bs(team_6_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_6.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_6))

                team_7_html = s.get("https://forkeeps.basketball.cbssports.com/teams/7")
                team_7_html.encoding = "utf-8"
                souped_team_7 = bs(team_7_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_7.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_7))

                team_8_html = s.get("https://forkeeps.basketball.cbssports.com/teams/8")
                team_8_html.encoding = "utf-8"
                souped_team_8 = bs(team_8_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_8.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_8))

                team_9_html = s.get("https://forkeeps.basketball.cbssports.com/teams/9")
                team_9_html.encoding = "utf-8"
                souped_team_9 = bs(team_9_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_9.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_9))

                team_10_html = s.get(
                    "https://forkeeps.basketball.cbssports.com/teams/10"
                )
                team_10_html.encoding = "utf-8"
                souped_team_10 = bs(team_10_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/team_10.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_team_10))

                all_players_html = s.get(self.config["league_allplayers_cy"])
                all_players_html.encoding = "utf-8"
                souped_all_players = bs(all_players_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/all_players.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_all_players))

                roster_2022_html = s.get(self.config["league_2022"])
                roster_2022_html.encoding = "utf-8"
                souped_roster_2022 = bs(roster_2022_html.text, "html.parser")
                html_path = Path(__file__).parent / "html/roster_2022.html"
                with html_path.open("w", encoding="utf-8") as file:
                    file.write(str(souped_roster_2022))

            self.logger.info(f"\nLAST HTML UPDATE: {datetime.now()}")

        def _pickle_updater():
            # UPDATE DF PICKLES
            pickled_league_df = self._league_builder()

            pickled_roster_df = self._roster_builder(
                Path(__file__).parent / "html/all_players.html"
            )

            pickled_roster_2022 = self._roster_builder(
                Path(__file__).parent / "html/roster_2022.html"
            ).drop(columns=["salary", "position", "contract"])

            pickled_zscores = self._zroster_builder(
                pickled_roster_df.drop(columns=["salary", "position", "contract"])
            )

            pickled_league_df, pickled_roster_df = self._additional_roster_filler(
                pickled_league_df, pickled_roster_df
            )

            pickled_league_df.to_pickle(
                Path(__file__).parent / "pickle/pickled_league_df.pkl"
            )
            pickled_roster_df.to_pickle(
                Path(__file__).parent / "pickle/pickled_roster_df.pkl"
            )
            pickled_roster_2022.to_pickle(
                Path(__file__).parent / "pickle/pickled_roster_2022.pkl"
            )
            pickled_zscores.to_pickle(
                Path(__file__).parent / "pickle/pickled_zscores.pkl"
            )

            self.logger.info(f"\nLAST PICKLE UPDATE: {datetime.now()}")

        def _weekly_totals_updater(refresh=False):
            def __login_sequence(destination_url):
                self.driver.get(
                    "https://www.cbssports.com/user/login/?redirectUrl=https%3A%2F%2Fwww.cbssports.com%2F%3Flogin%3Dconfirmed"
                )
                time.sleep(4)
                self.driver.find_element(By.ID, "app_login_username").send_keys(
                    os.getenv("CBS_USER")
                )
                self.driver.find_element(By.ID, "app_login_password").send_keys(
                    os.getenv("CBS_PASS")
                )
                self.driver.find_element(By.CLASS_NAME, "BasicButton").click()
                time.sleep(1)
                self.driver.get(destination_url)
                time.sleep(1)

            def __record_formatter(df, periods: list):
                df = df.astype(
                    {
                        "score": str,
                        "3pt": float,
                        "ast": float,
                        "bk": float,
                        "fgp": float,
                        "ftp": float,
                        "g": int,
                        "min": float,
                        "pts": float,
                        "st": float,
                        "to": float,
                        "trb": float,
                    }
                )
                df.set_index("team", inplace=True)
                return df

            # SELENIUM WEB DRIVER
            self.service = Service()
            self.options = webdriver.FirefoxOptions()
            self.options.add_argument("--headless")
            self.options.binary_location = r'/home/zbon/bin'
            self.driver = webdriver.Firefox(service=self.service, options=self.options)

            # Login to CBS
            __login_sequence(
                "https://forkeeps.basketball.cbssports.com/scoring/standard"
            )

            full_period = self.driver.find_element(
                By.CSS_SELECTOR, "div.select_div_label_container"
            ).text
            period_date = re.search(
                r"(?:([^,]*\,\s)){2}(.*?)(?=\))", full_period
            ).group(2)
            period_no = int(re.search(r"(?<=PERIOD\s).*(?=\s\()", full_period).group(0))
            full_date = datetime.strptime(
                str(period_date).replace(" ", "-") + "-" + str(datetime.today().year),
                "%b-%d-%Y",
            )

            # Update the config file with the current period
            with open(self.c_path, "r") as config_file:
                config = json.load(config_file)

            config.update({"league_period": f"{period_no}"})

            with open(self.c_path, "w") as config_file:
                config_file.write(json.dumps(config, indent=4))

            # Create a new DF
            record_df = pd.DataFrame()

            start_loop = 1
            if refresh == True:  # Full updating forced
                period_loop = period_no

            # Harvest the data
            cats = [
                "period",
                "team",
                "opponent",
                "score",
                "3pt",
                "ast",
                "bk",
                "fgp",
                "ftp",
                "g",
                "min",
                "pts",
                "st",
                "to",
                "trb",
                "period",
            ]

            # Start the harvest loop - p for periods, t for teams to iterate through the urls
            for p in range(start_loop, (period_loop + 1)):
                for t in range(1, 6):
                    self.driver.get(
                        f"https://forkeeps.basketball.cbssports.com/scoring/standard/{p}/{t}"
                    )
                    time.sleep(1)

                    # Arrange the stats for insertion into dictionary
                    away_scores = [
                        self.driver.find_element(By.ID, z).text
                        for z in ["awayocats" + str(y) for y in range(0, 11)]
                    ]
                    away_scores.insert(
                        0, self.driver.find_element(By.ID, "T_CAT_topSBAWAY").text
                    )
                    away_scores.insert(
                        1, self.driver.find_element(By.ID, "away_big_score").text
                    )
                    home_scores = [
                        self.driver.find_element(By.ID, z).text
                        for z in ["homeocats" + str(y) for y in range(0, 11)]
                    ]
                    home_scores.insert(
                        0, self.driver.find_element(By.ID, "T_CAT_topSBHOME").text
                    )
                    home_scores.insert(
                        1, self.driver.find_element(By.ID, "T_CAT_topSBAWAY").text
                    )
                    home_scores.insert(
                        2, self.driver.find_element(By.ID, "home_big_score").text
                    )
                    away_scores.insert(
                        1, self.driver.find_element(By.ID, "T_CAT_topSBHOME").text
                    )

                    # Insert periods
                    home_scores.insert(0, int(p))
                    away_scores.insert(0, int(p))

                    # Insert the entry into the dataframe
                    new_home = pd.DataFrame([{x: y for x, y in zip(cats, home_scores)}])
                    new_away = pd.DataFrame([{x: y for x, y in zip(cats, away_scores)}])

                    record_df = pd.concat([record_df, new_home], axis=0)
                    record_df = pd.concat([record_df, new_away], axis=0)

            self.driver.quit()

            # Apply the formatting function
            formatted_record_df = __record_formatter(
                record_df, list(range(1, (int(self.config["league_period"]) + 1)))
            )

            print(formatted_record_df)
            # Update the class record (the pickle loads occur on class init)
            self.league_record = formatted_record_df

            # Pickle
            formatted_record_df.to_pickle(
                Path(__file__).parent / "pickle/pickled_record.pkl"
            )

            # Log a successful update
            self.logger.info(f"\nLAST RECORD UPDATE: {datetime.now()}")

        _html_updater()
        _pickle_updater()
        _weekly_totals_updater(refresh=refresh)

    def session(self):
        with requests.Session() as s:
            s.post(self.config["login_url"], data=self.config["login_info"])
            return s

    # Builds the basic league info df on initialization
    def _league_builder(self):
        teams_exclusion_list = []
        df_output = pd.DataFrame(columns=self.config["tracked_datapoints"])

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

        df_output = pd.DataFrame(columns=self.config["tracked_statcats"])

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

            with open(
                Path(__file__).parent / f"html/team_{id}.html", "r", encoding="utf-8"
            ) as f:
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
            league["history"] = {"Record": ""}
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
    def _zroster_builder(self, roster, draft=False):

        # Pare the roster of players who haven't played games (avoid skewing zscores)
        roster = roster.loc[roster["g"] > 0]

        exclusions = ["player_name", "g", "zrank", "team_id"]

        data_refs = {
            str(x + "-avg"): None
            for x in self.config["tracked_zcats"]
            if x not in exclusions
        } | {
            str(x + "-stdev"): None
            for x in self.config["tracked_zcats"]
            if x not in exclusions
        }

        for x in self.config["tracked_zcats"]:
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
        z_df = pd.DataFrame(columns=self.config["tracked_zcats"])

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

        # Player zrank
        z_df["zrank"] = z_df.apply(
            lambda row: sum(
                [
                    row[x]
                    for x in self.config["tracked_zcats"]
                    if x not in exclusions and x != "fgp" and x != "ftp"
                ]
            ),
            axis=1,
        ).round(3)

        # Adjusted player zrank (takes punted cats into consideration)
        z_df["adj-zrank"] = z_df.apply(
            lambda row: sum(
                [
                    row[x]
                    for x in self.config["tracked_zcats"]
                    if x not in exclusions
                    and x not in self.punts
                    and x != "fgp"
                    and x != "ftp"
                ]
            ),
            axis=1,
        ).round(3)

        if draft == True:
            # Calculate relative $ value
            z_df["draft"] = z_df.apply(
                lambda row: (row["zrank"] / z_df["zrank"].sum())
                * self.config["league_total_budget"]
                * -1,
                axis=1,
            ).astype("int")

            # Calculate relative $ value
            z_df["adj-draft"] = z_df.apply(
                lambda row: (row["adj-zrank"] / z_df["adj-zrank"].sum())
                * self.config["league_total_budget"]
                * -1,
                axis=1,
            ).astype("int")
        else:
            pass

        # Normalize the zranks
        z_df["zrank"] = round(
            (z_df["zrank"] - z_df["zrank"].min())
            / (z_df["zrank"].max() - z_df["zrank"].min())
            * 100,
            0,
        ).astype("int")

        # Normalize the adjusted zranks
        z_df["adj-zrank"] = round(
            (z_df["adj-zrank"] - z_df["adj-zrank"].min())
            / (z_df["adj-zrank"].max() - z_df["adj-zrank"].min())
            * 100,
            0,
        ).astype("int")

        # Zrank dif (shows impact of punting cats)
        z_df["z-dif"] = z_df.apply(
            lambda row: (row["zrank"] - row["adj-zrank"]) * -1, axis=1
        ).round(3)

        if draft == True:
            # #Normalize the draft values
            z_df["draft"] = round(
                (z_df["draft"] - z_df["draft"].min())
                / (z_df["draft"].max() - z_df["draft"].min())
                * 65,
                0,
            ).astype("int")

            #  #Normalize the adjusted draft values
            z_df["adj-draft"] = round(
                (z_df["adj-draft"] - z_df["adj-draft"].min())
                / (z_df["adj-draft"].max() - z_df["adj-draft"].min())
                * 65,
                0,
            ).astype("int")
        else:
            pass

        # Cleanup the df
        z_df = z_df.drop(columns=["fgp", "ftp"]).rename(
            columns={"fgpg": "fg", "ftpg": "ft", "3ptpg": "3p"}
        )

        z_df.set_index(["player_name"], inplace=True)

        return z_df

    # Tool to lookup zranks (players and teams)
    def z(self, *args, cats=None):

        if cats:
            exclusions = ["g", "zrank", "player_name"]
            cats_list = list(
                [y for y in self.config["tracked_zcats"] if y not in exclusions]
            )
            if (
                any(
                    item in args
                    for item in self.config["tracked_zcats"]
                    if item not in exclusions
                )
                == True
            ):
                for x in args:
                    print(self.zscores.sort_values(by=x, ascending=True).tail(20))
            else:
                print(
                    f"No proper categories input; try one of the following: {cats_list}"
                )

        else:
            team_dict = {
                x: y
                for x, y in zip(
                    self.league_df.index.tolist(), self.league_df["team_id"].tolist()
                )
            }
            for x in args:
                # Check if it's a team.
                team_check = list(
                    filter(lambda y: x in y, self.league_df.index.tolist())
                )
                player_check = list(
                    filter(lambda y: x in y, self.zscores.index.tolist())
                )

                if len(team_check) == 0 and len(player_check) == 0:
                    continue
                elif len(team_check) == 1 and len(player_check) == 0:
                    print(
                        f"\nTEAM {team_check[0]}",
                        self.zscores.loc[
                            self.zscores["team_id"] == int(team_dict[team_check[0]])
                        ].sort_values(by="zrank"),
                    )
                elif len(team_check) > 0 and len(player_check) > 0:
                    print(
                        f"\nTEAM {team_check[0]}:\n",
                        self.zscores.loc[
                            self.zscores["team_id"] == int(team_dict[team_check[0]])
                        ].sort_values(by="zrank"),
                    )
                    if len(player_check) == 1:
                        print(
                            "\n",
                            self.zscores.loc[self.zscores.index == player_check[0]],
                        )
                    else:
                        for y in player_check:
                            print("\n", self.zscores.loc[self.zscores.index == y])
                elif len(player_check) == 1 and len(team_check) == 0:
                    print(self.zscores.loc[self.zscores.index == player_check[0]])
                elif len(player_check) > 1 and len(team_check) == 0:
                    for y in player_check:
                        print(self.zscores.loc[self.zscores.index == y])
                else:
                    pass


if __name__ == "__main__":
    # load config
    cbs_user = os.getenv("CBS_USER")
    cbs_pass = os.getenv("CBS_PASS")
    config_path = os.getenv("CBS_CONFIG")

    if not cbs_user and cbs_pass and config_path:
        print("Missing env values for CBS_USER / CBS_PASS / CBS_CONFIG")
        sys.exit(1)

    pd.set_option("mode.chained_assignment", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", None)

    cbs = CBS(cbs_user, cbs_pass, config_path)

    # cbs.update()

    # out = cbs._zroster_builder(cbs.roster_current)

    # print(cbs.league_record)
    # test = cbs.league_record.at['Fish', 'period_1']

    # print(week_totals(cbs.league_record, 1, 2))
    # print(cbs.league_record['period_2'])
    # print(cbs.roster_current)

    # print(week_totals(cbs.league_record, 1, 2).info())
    # test = week_totals(cbs.league_record, 1, 2).groupby('period')[['3pt', 'ast', 'bk']].aggregate('min', 'max')

    # test_2 = pd.concat([test.get_group(1), test.get_group(2)], axis=1)

    print(cbs.league_record)
