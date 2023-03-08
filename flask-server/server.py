from flask import Flask, request
import fastf1
import pandas as pd
import numpy as np
from flask_caching import Cache
import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


app.config['CACHE_DIR'] = os.path.join(app.root_path, 'cache')
fastf1.Cache.enable_cache(app.config['CACHE_DIR'])

cache = Cache(app, config={'CACHE_TYPE': 'simple'})


# app.config['CACHE_DIR'] = os.path.join(app.root_path, 'cache')

# fastf1.Cache.enable_cache(os.environ['FASTF1_CACHE_DIR'])

# cache = Cache(app, config={'CACHE_TYPE': 'simple'})
# cache_dir = 'C:/Users/ehan/Desktop/Learning/GreenGears-flask/flask-server/cache'
# fastf1.Cache.enable_cache(cache_dir)
# fastf1.Cache.enable_cache(
    
#     os.environ['F1_CACHE_PATH']
#     # 'C:/Users/ehan/Desktop/Learning/f1-tel/flask-server/venv'
#     )

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
@cache.memoize(timeout=60)
def get_session(year, schedule, event):
    session = fastf1.get_session(year, schedule, event)
    session.load()
    return session


@app.route("/schedule")
def schedule():
    selected_year = request.args.get('selectedYear')
    # print(type(int(selected_year)))
    schedule = fastf1.get_event_schedule(int(selected_year))
    now = datetime.date.today()
    schedule['Date'] = schedule['Session1Date'].dt.date
    schedule['Flag'] = schedule.apply(lambda row: 1 if row['Date'] <= now else 0, axis=1)
    schedule = schedule.loc[schedule['Flag'] == 1]
    return schedule["EventName"].to_dict()


@app.route("/lapData", methods=['GET'])
def lapData():
    global df
    selected_year = request.args.get('selectedYear')
    selected_Schedule = request.args.get('selectedSchedule')
    selected_Event = request.args.get('selectedEvent')
    # print(selected_year)
    session = get_session(int(selected_year), selected_Schedule, selected_Event)
    # session.load()
    Lapdata = session.laps
    df = Lapdata

    def convert_timedelta_to_mss(df):
        # select all columns of type timedelta64
        timedelta_cols = df.select_dtypes(include='timedelta64')

        # convert all timedelta columns to seconds
        for col in timedelta_cols.columns:
            df[col] = df[col].dt.total_seconds()

        # replace NaN values with 0
        df.fillna(0, inplace=True)

        # format the timedelta columns as m:s:ss
        for col in timedelta_cols.columns:
            df[col] = df[col].apply(
                lambda x: '{:02d}:{:06.4f}'.format(int(x // 60), x % 60))

        return df
    df = convert_timedelta_to_mss(df)
    df['LapTime'] = pd.to_timedelta('00:' + df['LapTime']).dt.total_seconds()
    df = df.loc[df['IsAccurate'] >= True]
    return df.to_dict()


@app.route("/driverData")
def driverData():
    selected_Year = request.args.get('selectedYear')
    selected_Schedule = request.args.get('selectedSchedule')
    selected_Event = request.args.get('selectedEvent')
    selected_Lap = request.args.get('selectedLap')
    driver_List = request.args.get('driverList')
    driver_List = driver_List.split(',')  # convert string to list
    print(f"The Selected driver is: {driver_List}")
    ddf = pd.DataFrame()
    session = get_session(int(selected_Year), selected_Schedule, selected_Event)
    # session.load()
    drivers = driver_List
    lap = int(selected_Lap)
    for driver in drivers:
        df1 = session.laps.pick_driver(driver)
        df = df1.loc[df1['LapNumber'] == lap]
        df = df.get_car_data().add_distance()
        df['LapNumber'] = lap
        df['Driver'] = driver
        ddf = pd.concat([ddf, pd.DataFrame(df)], ignore_index=True)
        # ddf = pd.merge(ddf, df1[['Driver', 'Team']], on='Driver')
    def convert_timedelta_to_mss(df):
        # select all columns of type timedelta64
        timedelta_cols = df.select_dtypes(include='timedelta64')

        # convert all timedelta columns to seconds
        for col in timedelta_cols.columns:
            df[col] = df[col].dt.total_seconds()

        # replace NaN values with 0
        df.fillna(0, inplace=True)

        # format the timedelta columns as m:s:ss
        for col in timedelta_cols.columns:
            df[col] = df[col].apply(
                lambda x: '{:02d}:{:06.4f}'.format(int(x // 60), x % 60))

        return df
    df = convert_timedelta_to_mss(ddf)
    
    return df.to_dict()

@app.route("/track")
def track():
    selected_Year = request.args.get('selectedYear')
    selected_Schedule = request.args.get('selectedSchedule')
    selected_Event = request.args.get('selectedEvent')
    selected_Lap = request.args.get('selectedLap')
    driver_List = request.args.get('driverList')
    driver_List = driver_List.split(',')  # convert string to list
    # driver_List = ['RIC', 'VER', 'HAM'] # list of drivers
    fastest_laps = []
    for driver in driver_List:
        session = fastf1.get_session(int(selected_Year), selected_Schedule, selected_Event)
        # session = get_session(int(selected_Year), selected_Schedule, selected_Event)
        # weekend = session.event
        session.load()
        lap = session.laps.pick_driver(driver).pick_fastest()
        x = lap.telemetry['X']
        y = lap.telemetry['Y']
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        # add driver column to the points array
        driver_col = np.full((len(points), 1, 1), driver)
        points = np.concatenate((points, driver_col), axis=2)
        fastest_laps.append(points)
    # concatenate the position data for all drivers
    fastest_points = np.concatenate(fastest_laps, axis=0)
    # sort the points by lap time
    sorted_points = fastest_points[np.argsort(fastest_points[:, 0, 2])]
    lst = sorted_points.tolist()
    my_dict = {'point{}'.format(i+1): lst[i][0] for i in range(len(lst))}
    return my_dict



if __name__ == "__main__":
    app.run()
