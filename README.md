# fantasybball-analytics

## cbs.py 
A class framework to scrape/update data for an online basketball fantasy pool. Updates are performed with the .update() function and stored in local html/pickle files.

## analytics.py
Functions for visualizing/analyzing pool data. These include: 

1) team_strengths(record (df from CBS class), team: str, period:list, multi=False (if true performs for entire league), Prankings=False (if true outputs text power rankings for league)
   * Outputs visualization of team(s) relative strength across various categories along with their total minutes in a given period(s).




# configuration
create a file named .config
CBS_USER="*email*"
CBS_PASS="*password*"
CBS_CONFIG = "*path to cbs-config.json file*



