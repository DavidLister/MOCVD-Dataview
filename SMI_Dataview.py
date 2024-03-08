# SMI_Dataview.py
#
# Tool for viewing the datalog files from the SMI Reactor
# David Lister
# August 2023
#

import plotly.graph_objects as go
import pandas as pd
import matplotlib.pyplot as plt
import glob
import time 

HEADER_ROW = 4

##fname = "S080_HT_GaN_Datalog 8-22-2018 2-01-21 PM.csv"
##fname = "S185_Datalog 6-21-2023 12-05-01 PM.csv"
##fname = "S187_Datalog 6-23-2023 12-34-01 PM.csv"
##fname = "S188_Datalog 7-11-2023 12-15-00 PM.csv"
##fname = "S189_Datalog 7-12-2023 2-58-15 PM.csv"
##fname = "S190_Datalog 7-14-2023 1-38-39 PM.csv"

initial_points = 0
compressed_points = 0

def compress(time, data):
    last_data = data[0]
    last_time = time[0]
    out_data = [last_data]
    out_time = [last_time]
    
    for i in range(len(time[1:])):
        if data[i+1] != last_data:
            if last_time != time[i]: 
                out_data.append(last_data)
                out_time.append(time[i])
            last_data = data[i+1]
            last_time = time[i+1]
            out_data.append(last_data)
            out_time.append(last_time)

    if out_time[-1] != time[time.index[-1]]:
        out_data.append(data[data.index[-1]])
        out_time.append(time[time.index[-1]])

##    print(f"Data compressed to {100 * len(out_data) / len(data):2.3f}%")
    global initial_points, compressed_points
    initial_points += len(data)
    compressed_points += len(out_data)
    return out_time, out_data

files = glob.glob("*.csv")
for fname in files:
    start_time = time.time()
    print(f"Starting {fname}")

    initial_points = 0
    compressed_points = 0
    
    df = pd.read_csv(fname, delimiter=',', parse_dates=True, header=HEADER_ROW)
    df = df.drop(df.columns[-1], axis=1)  # CSV has an extra comma per line
    df["Datetime"] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    columns_to_plot = numerical_columns

    AO1 = columns_to_plot.index("AO1")
    AI1 = columns_to_plot.index("AI1")
    cols = columns_to_plot[:min((AO1, AI1))]
    for i in range(80):
        cols.append(columns_to_plot[AO1 + i])
        cols.append(columns_to_plot[AI1 + i])
    columns_to_plot = cols

    for column in columns_to_plot:
        if column == "Layer":
            df[column] = df[column] * 100

        elif column[:2] == "DO":
            df[column] = df[column] * 100 - int(column[2:])

        elif column[:2] == "DI":
            df[column] = df[column] * 100 + int(column[2:])


    fig = go.Figure()
    for column in columns_to_plot:
        time_lst, data_lst = compress(df["Datetime"], df[column])
        fig.add_trace(go.Scatter(x=time_lst, y=data_lst, mode="lines", name=column))

    fig.update_layout(
        title=go.layout.Title(
            text=f"SMI Growth Data<br><sup>{fname}</sup>",
            xref="paper",
            x=0)
        )

    out = fig.to_html()

    with open(fname[:4] + "-v01.html", 'w', encoding="utf-8") as f:
        f.write(out)

    print(f"Completed in {time.time() - start_time:.2f} seconds with a compression ratio of {initial_points/compressed_points:.2f}")

