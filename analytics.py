import requests
import regex as re
import pandas as pd
import cbs
import os
import statistics
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib as mpl
import warnings
from pathlib import Path

#%matplotlib inline

# Various analytic functions
def team_strengths(record, team: str, period: list, multi=False):

    # Process teams one by one as-needed
    def _team_processor(record, team: str, period: list):

        columns = [
            "3pt",
            "ast",
            "bk",
            "fgp",
            "ftp",
            "pts",
            "st",
            "to",
            "trb",
            "max",
            "min",
            "team",
            "mins",
            "period",
        ]
        cats = ["3pt", "ast", "bk", "fgp", "ftp", "pts", "st", "to", "trb"]

        graph_df = pd.DataFrame(columns=columns)

        for p in period:
            working_df = record.loc[record["period"] == period[p - 1]]
            team_totals = working_df.loc[team]

            # Convert to z/standard score
            new_row = {
                "3pt": round(
                    (team_totals["3pt"] - working_df["3pt"].mean())
                    / working_df["3pt"].std(),
                    1,
                ),
                "ast": round(
                    (team_totals["ast"] - working_df["ast"].mean())
                    / working_df["ast"].std(),
                    1,
                ),
                "bk": round(
                    (team_totals["bk"] - working_df["bk"].mean())
                    / working_df["bk"].std(),
                    1,
                ),
                "fgp": round(
                    (team_totals["fgp"] - working_df["fgp"].mean())
                    / working_df["fgp"].std(),
                    1,
                ),
                "ftp": round(
                    (team_totals["ftp"] - working_df["ftp"].mean())
                    / working_df["ftp"].std(),
                    1,
                ),
                "pts": round(
                    (team_totals["pts"] - working_df["pts"].mean())
                    / working_df["pts"].std(),
                    1,
                ),
                "st": round(
                    (team_totals["st"] - working_df["st"].mean())
                    / working_df["st"].std(),
                    1,
                ),
                "to": round(
                    (team_totals["to"] - working_df["to"].mean())
                    / working_df["to"].std(),
                    1,
                )
                * -1,
                "trb": round(
                    (team_totals["trb"] - working_df["trb"].mean())
                    / working_df["trb"].std(),
                    1,
                ),
            }

            # Fill in the rest of the dictionary
            new_row.update(
                {
                    "max": max(new_row.values()),
                    "min": min(new_row.values()),
                    "team": team,
                    "mins": team_totals["min"],
                    "period": p,
                }
            )

            # Normalize the scores for graphing
            for c in cats:
                # Get rid of the negatives (add the additional .2 just to ensure the stat represented in the graph)
                new_row.update({c: round(new_row[c] + abs((new_row["min"] * 1.2)), 1)})

            # Convert back to df
            graph_df = (
                pd.concat([graph_df, pd.DataFrame(new_row, index=[team])])
                .drop(columns=["max", "min", "team", "mins"])
                .astype({"period": int})
            )

        graph_df.index = graph_df["period"]
        graph_df.drop(columns=["period"], inplace=True)

        return graph_df

    if str(team) not in record.index:
        print("Team not recognized")
        return

    # Plot the results (One way)
    color_map = [
        "#0f668f",
        "#6182af",
        "#9a9fcc",
        "#cfbee6",
        "#ffdfff",
        "#f7b8e0",
        "#f190b8",
        "#e76787",
        "#de425b",
    ]

    if multi == True:
        fig, ax = plt.subplots(3, 3, figsize=(20, 14))
        plt.subplots_adjust(hspace=0.5)
        plt.suptitle("Relative Cat Strengths")

        # Drop my own team (will be in a different pop-up)
        temp_record = record.drop("Taints", axis=0)

        for n, team in enumerate(
            temp_record.loc[temp_record["period"] == period[0]].index
        ):
            graph_df = _team_processor(record, team, period)
            position_list = [
                [0, 0],
                [0, 1],
                [0, 2],
                [1, 0],
                [1, 1],
                [1, 2],
                [2, 0],
                [2, 1],
                [2, 2],
            ]

            stacks = ax[position_list[n][0]][position_list[n][1]].axes.stackplot(
                graph_df.index,
                graph_df["3pt"],
                graph_df["ast"],
                graph_df["bk"],
                graph_df["fgp"],
                graph_df["ftp"],
                graph_df["pts"],
                graph_df["st"],
                graph_df["to"],
                graph_df["trb"],
                colors=color_map,
                edgecolor="black",
                linewidth=0.5,
            )

            ax[position_list[n][0]][position_list[n][1]].axes.set_xticks(graph_df.index)

            # Add a minutes line
            ax2 = ax[position_list[n][0]][position_list[n][1]].twinx()
            ax2.plot(graph_df.index, record["min"].loc[team], "--", scaley=True)

            last_y = 0
            for stack, category in zip(stacks, graph_df.columns):
                p = stack.get_paths()[0]
                mask = (
                    p.vertices[:, 0] == period[-1]
                )  # Gets the final period (right-most side of x-axis)
                filtered_values = p.vertices[mask][:, 1]
                new_y = filtered_values.max()
                y = statistics.median(
                    [last_y, new_y]
                )  # Finds position between last value and current value
                x = period[-1]
                ax[position_list[n][0]][position_list[n][1]].annotate(
                    f"{category.upper()}", xy=(x, y), color="black", fontsize=10
                )
                last_y = new_y

            plt.subplots_adjust(left=0.1, right=2, top=0.9, bottom=0.1)
            ax[position_list[n][0]][position_list[n][1]].axes.set_title(team)

        plt.tight_layout()
        plt.savefig(Path(__file__).parent / "images/team_strength_field.png")

        # Plot my team for comparison
        fig, ax = plt.subplots(figsize=(8, 6))

        graph_df = _team_processor(record, "Taints", period)

        stacks = plt.stackplot(
            graph_df.index,
            graph_df["3pt"],
            graph_df["ast"],
            graph_df["bk"],
            graph_df["fgp"],
            graph_df["ftp"],
            graph_df["pts"],
            graph_df["st"],
            graph_df["to"],
            graph_df["trb"],
            colors=color_map,
            edgecolor="black",
            linewidth=0.5,
        )

        last_y = 0
        for stack, category in zip(stacks, graph_df.columns):
            p = stack.get_paths()[0]
            mask = p.vertices[:, 0] == period[-1]
            filtered_values = p.vertices[mask][:, 1]
            new_y = filtered_values.max()
            y = statistics.median([last_y, new_y])
            x = period[-1]
            plt.annotate(f"{category.upper()}", xy=(x, y), color="black", fontsize=10)
            last_y = new_y

        plt.subplots_adjust(left=0.1, right=1.5, top=0.9, bottom=0.1)
        plt.xticks(graph_df.index)
        plt.title("Taints")

        # Add a minutes line
        ax2 = ax.twinx()
        ax2.plot(graph_df.index, record["min"].loc["Taints"], "--", scaley=True)

        plt.tick_params(left=False, right=False)
        plt.tight_layout()
        plt.savefig(Path(__file__).parent / "images/team_strength_taints.png")

    # Single plot
    else:
        graph_df = _team_processor(record, team, period)

        fig, ax = plt.subplots(figsize=(8, 6))

        stacks = plt.stackplot(
            graph_df.index,
            graph_df["3pt"],
            graph_df["ast"],
            graph_df["bk"],
            graph_df["fgp"],
            graph_df["ftp"],
            graph_df["pts"],
            graph_df["st"],
            graph_df["to"],
            graph_df["trb"],
            colors=color_map,
            edgecolor="black",
            linewidth=0.5,
        )

        last_y = 0

        for stack, category in zip(stacks, graph_df.columns):
            p = stack.get_paths()[0]
            mask = p.vertices[:, 0] == period[-1]
            filtered_values = p.vertices[mask][:, 1]
            new_y = filtered_values.max()
            y = statistics.median([last_y, new_y])
            x = period[-1]
            plt.annotate(f"{category.upper()}", xy=(x, y), color="black", fontsize=10)
            last_y = new_y

        ax2 = ax.twinx()
        ax2.plot(graph_df.index, record["min"].loc[team], "--", scaley=True)

        plt.subplots_adjust(left=0.1, right=1.5, top=0.9, bottom=0.1)
        plt.tick_params(left=False)
        plt.title(team)

        plt.tight_layout()
        plt.savefig(Path(__file__).parent / f"images/team_strength_{team}.png")


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
    warnings.filterwarnings("ignore")

    cbs = cbs.CBS(cbs_user, cbs_pass, config_path)

    cbs.update(refresh=True)

    team_strengths(cbs.league_record, "Boom", [1, 2], multi=True)
