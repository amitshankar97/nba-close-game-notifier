try:
    import requests
    import os
    from db import DB

    CONFIG = {
        'pt_differential': 10,
        'mins_left': 6,
        'period': 4
    }

    MAKER_URL = os.environ['MAKER_URL']
    NBA_BASE = 'https://data.nba.net/10s'
    INTERESTING_TEAMS = ['LAL', 'BOS', 'DAL', 'DEN', 'GSW', 'HOU', 'LAC', 'MEM', 'MIL', 'OKC', 'PHI', 'POR', 'TOR', 'UTA']

    def sendNotification(team1, team2, time):
        payload = {
            'value1': team1,
            'value2': team2,
            'value3': time
        }

        r = requests.post(MAKER_URL, data=payload)

    def NBATodayScoreboard():
        r = requests.get(NBA_BASE + '/prod/v2/today.json').json()
        todayScoreboard = r['links']['todayScoreboard']
        return requests.get(NBA_BASE + todayScoreboard).json()

    def logToMongo():
        mongo = DB()
        mongo.logToMongo()

    if __name__ == '__main__':
        scoreboard = NBATodayScoreboard()
        games = scoreboard['games']

        logToMongo()

        for game in games:

            home = game['hTeam']
            away = game['vTeam']

            if home['triCode'] in INTERESTING_TEAMS or away['triCode'] in INTERESTING_TEAMS:
                if game['isGameActivated'] and game['period']['current'] >= CONFIG['period']:

                    clock = game['clock'].split(':')
                    
                    if len(clock) < 2:
                        minutes = 0
                    else:
                        minutes = int(clock[0])

                    pts_difference = abs(int(home['score']) - int(away['score']))

                    current_period = game['period']['current']
                    period = ""
                    if current_period > 4:
                        period = (str(current_period % 4) + 'OT')
                    else:
                        period = str(current_period) + 'Q'

                    if minutes <= CONFIG['mins_left'] and pts_difference <= CONFIG['pt_differential']:
                        try:
                            mongo = DB()
                            db_game = mongo.find_game(game['gameId'])

                            if db_game == None:
                                time_left = period + ' ' + game['clock']

                                home_text = home['triCode'] + ' ' + str(home['score'])
                                away_text = away['triCode'] + ' ' + str(away['score'])

                                sendNotification(home_text, away_text, time_left)
                                mongo.insert_game(game['gameId'])
                            else:
                                continue

                        except Exception as e:
                            mongo = DB()
                            mongo.logException(e)

except Exception as e:
    mongo = DB()
    mongo.logException(e)