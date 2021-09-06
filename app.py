# Jerry Day
# 8/25/2021

import os
import re
import base64
import io
import datetime
from datetime import timedelta

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.express as px

import pandas as pd

# my imports
import createschedules

# make the schedules
createschedules.check_and_make_schedules()                                   # ************** uncomment ****************

# Create dropdown
schedules =[f for f in os.scandir('Schedules') if f.is_file() & bool(re.search('.+\.csv$',f.name))]

dd_options = [ {'label' : re.search('^(.+?)_Schedule\.csv', f.name).group(1) , 'value' : f.path } for f in schedules]

# table columns ... They are imbedded in the code too.  Sorry
table_columns = [{'name':c, 'id':c} for c in ['Movie', 'Theater', 'StartTime', 'EndTime', 'Runtime']]

# create app.
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    # Title and explanation div
    html.Div([
        html.H1('Movie Scheduler Prototype'),
        html.H3('Jerry Day'),
        html.Div(html.P('Generate a daily schedule for movies from a pair of uploaded CVS files containing information about (1) theaters and (2) movies.  The schedules are optimized to maximize the total number of showings and distribute the movie start times.  Select a schedule from the dropdown to update the display.  The schedule can be downloaded from the button below the gantt chart.'),
                style = {'width' : '45%', 'textAlign' : 'justify'})
    ]),
    # Dropdown and upload/download div
    html.Div([
        html.Div(dcc.Dropdown(id='schedule_dd', 
                     options=dd_options,
                     value='Schedules\\First-Test_Schedule.csv'
                    ),
                 style = {'display':'inline-block', 'width': '25%'}),
        html.Div(dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Upload Disabled: Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                       'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10%'
                    },
                    # Allow multiple files to be uploaded
                    multiple=True
                    ),
                 style = {'display':'inline-block', 'width': '30%'}),
    ]),
    html.Div([
        dcc.Graph(id='schedule_gantt')
    ]),
    dash_table.DataTable(
        id='table',
        columns=table_columns,
#        data=df.to_dict('records'),
        export_format='xlsx'
    ),
    html.Div(id='output-data-upload')
])

# Callbacks


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        df = pd.DataFrame()
        if filename.endswith('.csv'):
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith('.xlsx'):
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        if df.empty:
            result_div = html.Div("The uploaded file must end in '.csv' and have data.")
        else:
            result_div = html.Div([
                html.H5(filename),
                html.H6(datetime.datetime.fromtimestamp(date)),

                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in df.columns]
                ),

                html.Hr(),  # horizontal line

                # For debugging, display the raw contents provided by the web browser
                html.Div('Raw Content'),
                html.Pre(contents[0:200] + '...', style={
                    'whiteSpace': 'pre-wrap',
                    'wordBreak': 'break-all'
                })
            ])
    except Exception as e:
        print(e)
        result_div = html.Div([
            'There was an error processing this file.'
        ])

    return result_div


@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

    
@app.callback(
    [Output("schedule_gantt", "figure"), Output("table", "data")],
    [Input("schedule_dd", "value")])
def update_gantt_chart(f_path):
    df = pd.read_csv(f_path)
    df.startTimeDate = pd.to_datetime(df.startTimeDate)
    df.endTimeDate = pd.to_datetime(df.endTimeDate)
    
    #create df for gantt chart
    movie_fig = df[['theatre','startTimeDate', 'endTimeDate', 'movie']].copy()
    movie_fig.rename(mapper = {'theatre' : 'Task','startTimeDate' : 'Start','endTimeDate' : 'Finish','movie' : 'Resource'}, axis = 'columns', inplace = True)

    trailer_fig = df[['theatre','startTimeDate', 'endTimeDate', 'Trailers']].copy()
    trailer_fig.rename(columns = {'theatre':'Task'}, inplace = True)
    trailer_fig['Start'] = trailer_fig['startTimeDate'] - pd.to_timedelta(trailer_fig['Trailers'], "m")
    trailer_fig['Finish'] = trailer_fig['startTimeDate']
    trailer_fig['Resource'] = 'Trailer'
    trailer_fig = trailer_fig.drop(columns = ['startTimeDate', 'endTimeDate', 'Trailers'])

    ads_fig = df[['theatre','startTimeDate', 'endTimeDate', 'Trailers', 'Pre_Show_Advertising']].copy()
    ads_fig.rename(columns = {'theatre':'Task'}, inplace = True)
    ads_fig['Start'] = ads_fig['startTimeDate'] - pd.to_timedelta(ads_fig['Trailers'], "m") - pd.to_timedelta(ads_fig['Pre_Show_Advertising'], "m")
    ads_fig['Finish'] = ads_fig['startTimeDate'] - pd.to_timedelta(ads_fig['Trailers'], "m")
    ads_fig[['Resource']] = 'Ads'
    ads_fig = ads_fig.drop(columns = ['startTimeDate', 'endTimeDate', 'Trailers', 'Pre_Show_Advertising'])

    clean_fig = df[['theatre','startTimeDate', 'endTimeDate', 'Post_Clean_Time']].copy()
    clean_fig.rename(columns = {'theatre':'Task'}, inplace = True)
    clean_fig['Start'] = clean_fig['endTimeDate']
    clean_fig['Finish'] = clean_fig['endTimeDate'] + pd.to_timedelta(clean_fig['Post_Clean_Time'], "m")
    clean_fig[['Resource']] = 'Cleaning'
    clean_fig = clean_fig.drop(columns = ['startTimeDate', 'endTimeDate', 'Post_Clean_Time'])
    
    fig = px.timeline(movie_fig.append(trailer_fig).append(ads_fig).append(clean_fig), 
                      x_start="Start", x_end="Finish", y="Task", color="Resource", text = "Resource",
                      title="Daily Movie Schedule for '" + re.search('Schedules\\\\(.*?)_Schedule\.csv$', f_path).group(1) + "'",
                      labels={"Task" : "Theater", "Resource" : "Movie"})
    # fig.update_traces(textposition = 'inside')
    fig.update_layout(title_font = dict(size = 30))
    fig.update_layout(showlegend=False)
    
    table_columns_list = [d['id'] for d in table_columns]
    table_df = df.rename(mapper = {'theatre' : 'Theater','startTimeDate' : 'StartTime','endTimeDate' : 'EndTime','movie' : 'Movie', 'Runtime' : 'Runtime'}, 
                         axis = 'columns'
                        )[table_columns_list]
    table_formatted = table_df.to_dict('records')
    
    return fig, table_formatted

if __name__ == '__main__':
    app.run_server(debug=True)
