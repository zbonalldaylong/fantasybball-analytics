import requests
import regex as re
import pandas as pd
import cbs
import os
import sys
import statistics
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib as mpl
import warnings
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
#%matplotlib inline

def team_strengths(record, team:str, period:list, multi=False, Prankings=False):
    
    """Outputs relative stat strengths of all teams; outputs power rankings with Prankings toggle"""
    
    def _team_processor(record, l_team:str, period:list):
        
        """Processes teams as needed; converts stat totals to standard z scores and normalizes negative values"""
        
        columns = ['3pt', 'ast', 'bk', 'fgp', 'ftp', 'pts', 'st', 'to', 'trb', 'max', 'min', 'team', 'mins', 'period']
        cats = ['3pt', 'ast', 'bk', 'fgp', 'ftp', 'pts', 'st', 'to', 'trb']
        
        graph_df = pd.DataFrame(columns=cats)
        
        for p in period:
        
            working_df = record.loc[record['period'] == p].drop(columns=['opponent', 'score', 'period'])
            
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(working_df).round(2) + 0.2
            
            normalized_period = pd.DataFrame(data=scaled, columns=working_df.columns, index=working_df.index)
            normalized_period['period'] = p
            
            #Convert back to df
            graph_df = pd.concat([graph_df, normalized_period]).astype({'period':int})
        
        #Output a given team
        graph_df = graph_df.loc[graph_df.index == l_team]
        
        
        graph_df.index = graph_df['period']
        graph_df.drop(columns=['period'], inplace=True)
        
        return graph_df

    def _prankings():
        
        """ Calculates power rankings based on standardized strengths across cats """

        output_df = pd.DataFrame(columns=record.loc[record['period'] == period[-1]].index, index=period)
        for p in period:
            for man in output_df.columns:      
                #print(f'{man}', _team_processor(record, man, period))
                output_df.at[p, man] = _team_processor(record, man, period).loc[p].sum().round(1)
            
        
        print('\n\n',output_df,'\n\n')

        return output_df
    
    if str(team) not in record.index:
        print('Team not recognized')
        return
    
    #Output power-rankings if Prankings toggle true. 
    if Prankings == True:
        _prankings()
        return
    
    #If plotting the results (Prankings == False)
    color_map = ['#0f668f', '#6182af', '#9a9fcc', '#cfbee6', '#ffdfff', '#f7b8e0', '#f190b8', '#e76787', '#de425b']
    
    
    if multi == True:
        fig, ax = plt.subplots(3, 3, figsize=(22, 16))
        plt.subplots_adjust(hspace=0.5)
        plt.suptitle('Relative Cat Strengths')
        
        #Drop my own team (will be in a different pop-up)
        temp_record = record.drop('Taints', axis=0)
        
        #Establish the timeframe for minutes based on argument input
        timeframe = record.loc[record['period'].isin(period)]
        timeframe = timeframe[['min', 'period']]
        
        for n, z_team in enumerate(temp_record.loc[temp_record['period'] == period[0]].index):
            graph_df = _team_processor(record, z_team, period)
            position_list = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]

            stacks = ax[position_list[n][0]][position_list[n][1]].axes.stackplot(graph_df.index,
                                    graph_df['3pt'], graph_df['ast'], graph_df['bk'], graph_df['fgp'], graph_df['ftp'],
                                    graph_df['pts'], graph_df['st'], graph_df['to'], graph_df['trb'],
                                    colors=color_map, edgecolor='black', linewidth=0.5)
            
            ax[position_list[n][0]][position_list[n][1]].axes.set_xticks(graph_df.index)
            
            #Add a minutes line
            ax2 = ax[position_list[n][0]][position_list[n][1]].twinx()
            #print(graph_df.index, '\n\n')
            #print(record['min'].loc['Taints'])
            
            ax2.plot(graph_df.index, timeframe['min'].loc[z_team], '--', scaley=True)
            ax2.set_ylim(850, 1450)
            
            last_y = 0
            
            for stack, category in zip(stacks, graph_df.columns):
                p = stack.get_paths()[0]
                mask = p.vertices[:,0] == period[-1] #Gets the final period (right-most side of x-axis)
                filtered_values = p.vertices[mask][:,1]
                new_y = filtered_values.max() 
                y = statistics.median([last_y, new_y]) #Finds position between last value and current value
                x = period [-1] 
                ax[position_list[n][0]][position_list[n][1]].annotate(f'{category.upper()}', xy=(x, y), color='black', fontsize=10)
                last_y = new_y
            
            plt.subplots_adjust(left=0.1, right=2, top=0.9, bottom=0.1)
            ax[position_list[n][0]][position_list[n][1]].axes.set_title(z_team)

        plt.tight_layout()
        plt.savefig(Path(__file__).parent / "images/team_strength_field.png")
        
        
        #Plot my team for comparison
        fig, ax = plt.subplots(figsize=(8,6))
        
        graph_df = _team_processor(record, 'Taints', period)
        
        stacks = plt.stackplot(
        graph_df.index,
        graph_df['3pt'], graph_df['ast'], graph_df['bk'], graph_df['fgp'], graph_df['ftp'],
        graph_df['pts'], graph_df['st'], graph_df['to'], graph_df['trb'],
        colors=color_map, edgecolor='black', linewidth=0.5)
        
        last_y = 0
        for stack, category in zip(stacks, graph_df.columns):
            p = stack.get_paths()[0]
            mask = p.vertices[:,0] == period[-1]
            filtered_values = p.vertices[mask][:,1]
            new_y = filtered_values.max() 
            y = statistics.median([last_y, new_y])
            x = period [-1] 
            plt.annotate(f'{category.upper()}', xy=(x, y), color='black', fontsize=10)
            last_y = new_y
            
        plt.subplots_adjust(left=0.1, right=1.5, top=0.9, bottom=0.1)
        plt.xticks(graph_df.index)
        plt.title('Taints')
        

        #Add a minutes line
        ax2 = ax.twinx()
        ax2.plot(graph_df.index, timeframe['min'].loc['Taints'], '--', scaley=True)
        ax2.set_ylim(850, 1450)
        
        plt.tick_params(left=False, right=False) 
        plt.tight_layout()
        plt.savefig(Path(__file__).parent / "images/team_strength_taints.png")
    
    
    #Single plot
    else:
        graph_df = _team_processor(record, team, period)
        
        fig, ax = plt.subplots(figsize=(8,6))
        
        stacks = plt.stackplot(
        graph_df.index,
        graph_df['3pt'], graph_df['ast'], graph_df['bk'], graph_df['fgp'], graph_df['ftp'],
        graph_df['pts'], graph_df['st'], graph_df['to'], graph_df['trb'],
        colors=color_map, edgecolor='black', linewidth=0.5)
        
        last_y = 0
        
        for stack, category in zip(stacks, graph_df.columns):
            p = stack.get_paths()[0]
            mask = p.vertices[:,0] == period[-1]
            filtered_values = p.vertices[mask][:,1]
            new_y = filtered_values.max() 
            y = statistics.median([last_y, new_y])
            x = period [-1] 
            plt.annotate(f'{category.upper()}', xy=(x, y), color='black', fontsize=10)
            last_y = new_y
            
        ax2 = ax.twinx()
        ax2.plot(graph_df.index, record['min'].loc[team], '--', scaley=True)
        ax2.set_ylim(850, 1450)
        
        plt.subplots_adjust(left=0.1, right=1.5, top=0.9, bottom=0.1)
        plt.tick_params(left=False) 
        plt.title(team)
        
        plt.tight_layout()
        plt.savefig(Path(__file__).parent / f"images/team_strength_{team}.png")

def snapshot(record, team: str, period: list):
    """ This is a function that assesses a team's performance cat-by-cat against the league over a specified period """
    
    cats_m = ['min', '3pt', 'ast', 'bk', 'fgp', 'ftp', 'pts', 'st', 'to', 'trb']
    cats = ['3pt', 'ast', 'bk', 'fgp', 'ftp', 'pts', 'st', 'to', 'trb']
    
    if str(team) not in record.index:
        print('Team not recognized')
        return
    
    if len(period) < 2:
        print('More than one period required')
        return
    
    #Outputs the necessary data: team total, max, min for each cat in the specified timeframe
    def _df_processor(record, team:str, period:list):
        cats = ['min', '3pt', 'ast', 'bk', 'fgp', 'ftp', 'pts', 'st', 'to', 'trb']

        team_totals = record.loc[team].set_index('period').drop(columns=['opponent', 'score'])
        
        #weekly minimums and maximums of various stat categories
        weekly_totals = record.groupby('period')[['3pt', 'ast', 'bk', 'fgp', 'ftp', 'pts', 'st', 'to', 'trb']].agg(['min', 'max'])
        
        graph_df = pd.DataFrame()
        
        for p in period:
            #All of the teams weekly stats
            all_team_totals = record.loc[record['period'] == p]
            
            weekly_totals_slice = weekly_totals.loc[weekly_totals.index == p]
            
            
            team_totals_slice = team_totals.loc[team_totals.index == p]

            #Totals
            for cat in cats_m:
                weekly_totals_slice[f'{cat}-t'] = team_totals_slice[cat]
    
            #median
                weekly_totals_slice[f'{cat}-m'] = all_team_totals[cat].median()
    
            graph_df = pd.concat([graph_df, weekly_totals_slice])
            
        return graph_df
    
    graph_df = _df_processor(record, team, period)
    
    #Create the plot
    fig, ax = plt.subplots(3, 3, figsize=(22, 16))
    plt.subplots_adjust(hspace=0.5)
    plt.suptitle(f'Cat Snapshot for {team} (Periods {period[0]} - {period[-1]})\n\n', fontsize=16)
    
    position_list = [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]
    
    for n, cat in enumerate(cats):
    
        #Min/max
        max = sns.lineplot(x=graph_df.index, y=graph_df[cat]['max'], ax=ax[position_list[n][0]][position_list[n][1]], color='#191970', alpha=0.3)
        min = sns.lineplot(x=graph_df.index, y=graph_df[cat]['min'], ax=ax[position_list[n][0]][position_list[n][1]], color='#191970', alpha=0.3)
        
        #Shade between them
        line = min.get_lines()
        ax[position_list[n][0]][position_list[n][1]].fill_between(line[0].get_xdata(), line[0].get_ydata(), line[1].get_ydata(), label=f'{cat.upper()} Range', color='#A5C4D4', alpha=0.3)
        
        #Team total 
        total = sns.lineplot(x=graph_df.index, y=graph_df[f'{cat}-t'], label=f'{team} Total', ax=ax[position_list[n][0]][position_list[n][1]], color='#FF9912', linewidth=2.5)
        
        #League median
        lmedian = sns.lineplot(x=graph_df.index, y=graph_df[f'{cat}-m'], label='League Median', ax=ax[position_list[n][0]][position_list[n][1]], alpha=0.75, color='#A1869E', linestyle='dotted', linewidth=2.5)
        
        #Set x-axis ticks to graph index (periods)
        ax[position_list[n][0]][position_list[n][1]].set(ylabel='', xlabel='')
        ax[position_list[n][0]][position_list[n][1]].axes.set_xticks(graph_df.index)
        ax[position_list[n][0]][position_list[n][1]].axes.set_title(cat.upper())
        ax[position_list[n][0]][position_list[n][1]].legend().set_visible(True)
        
    
    plt.tight_layout()
    plt.savefig("images/team_snapshot.png")

def faceoff(record, team:str, period:list):
    """ Runs hypothetical matchups for a team against the field over specified periods; takes df for record input"""
    
    cats = ['3pt', 'ast', 'bk', 'fgp', 'ftp', 'pts', 'st', 'to', 'trb']
    
    if str(team) not in record.index:
        print('Team not recognized')
        return
    
    team_total = record.loc[team].set_index('period').drop(columns=['opponent', 'score'])
    field = record.loc[record['period'] == 1].index.to_list()
    field.remove(team)
    
    wins = 0
    wins_list = []
    losses = 0
    losses_list = []
    ties = 0
    ties_list = []
    
    for p in period:
        team_total_slice = team_total.iloc[p - 1]
        record_slice = record.loc[record['period'] == (p)]
        
        for opp in field:
            for cat in cats:
                #print(f'{p} -- {opp} -- {cat}\n\n total 1: {team_total_slice[cat]} total 2: {record_slice.at[opp, cat]}')
                #print(wins_list)
                if cat != 'to':
                    if team_total_slice[cat] > record_slice.at[opp, cat]:
                        #print(f'WIN ', team_total_slice[cat], 'v ', record_slice.at[opp, cat])
                        wins += 1
                        wins_list.append(cat)
                    elif team_total_slice[cat] == record_slice.at[opp, cat]:
                        ties += 1
                        ties_list.append(cat)
                    elif team_total_slice[cat] < record_slice.at[opp, cat]:
                        losses += 1
                        losses_list.append(cat)
                else:
                    if team_total_slice[cat] < record_slice.at[opp, cat]:
                        wins += 1
                        wins_list.append(cat)
                    elif team_total_slice[cat] == record_slice.at[opp, cat]:
                        ties += 1
                        ties_list.append(cat)
                    elif team_total_slice[cat] > record_slice.at[opp, cat]:
                        losses += 1
                        losses_list.append(cat)
                
                result = 'win' if wins > losses else 'tie' if wins == losses else 'lose'
            
            print(f'period {p} matchup between {team} and {opp}, {team} would {result} {wins}-{losses}-{ties}')
            wins = 0
            losses = 0
            ties = 0
            wins_list.clear()
        print('\n')



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
    
    period_range = [1, 2, 3, 4, 5, 6]

    