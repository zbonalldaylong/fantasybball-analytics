# fantasybball-analytics

## cbs.py 
A class framework to scrape/update data for an online basketball fantasy pool. Updates are performed with the .update() function and stored in local html/pickle files.

## analytics.py
Functions for visualizing/analyzing pool data. These include: 

1) **team_strengths(record (df from CBS class), team: str, period:list, multi=False (if true performs for entire league), Prankings=False (if true outputs text power rankings for league)**
   * Outputs visualization of team(s) relative strength across various categories along with their total minutes in a given period(s).
<br>

![team_strengths output (teams blanked out)](https://github.com/zbonalldaylong/fantasybball-analytics/assets/77871506/23778633-e882-4dc9-84fb-aca5b5255b37)
<br>
<br>
<br>
2) **snapshot(record (df from CBS class), team:str, period:list)**
   * Outputs a visual rundown of a team's category-by-category performance across specified periods.

<br>

![snapshot output](https://github.com/zbonalldaylong/fantasybball-analytics/assets/77871506/d669dea0-6f4e-4da1-bcf9-56e6f4a4b33d)
<br>
<br>
<br>
3) **faceoff(record, team:str, period:list)**
  * Assesses a team's weekly results against a hypothetical matchup against each other team in the field; outputs what the score would have been had they matched up. 
<br>

# configuration
create a file named .config
CBS_USER="*email*"
CBS_PASS="*password*"
CBS_CONFIG = "*path to cbs-config.json file*



