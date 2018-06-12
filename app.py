#===========================================================================================
# Milestone project for "The Data Incubator"

# Written by
# Abhijith Rajan
# 07/12/2018

#===========================================================================================
from flask import Flask, render_template, request, redirect

#from dotenv import load_dotenv, find_dotenv
#load_dotenv(find_dotenv())

import os
from datetime import datetime, timedelta
import requests
import pandas as pd

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.embed import components
#===========================================================================================

app = Flask(__name__)

#===========================================================================================
@app.route('/', methods=['GET','POST'])
def index():
    pars = {}
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        pars['symbl'] = request.form['ticker']
        try:
            pars['start'] = datetime.strptime(request.form['start'], "%Y-%m-%d")
        except:
            return render_template("error_time_stamp.html",errors="wrong datetime format")
        try:
            pars['stop'] = datetime.strptime(request.form['stop'], "%Y-%m-%d")
        except:
            return render_template("error_time_stamp.html",errors="the wrong datetime format")
        if pars['start'] >= pars['stop']:
            return render_template("error_time_stamp.html",errors="the start date is great than the stop date")
        if pars['stop'] > datetime(2018,3,27):
            return render_template("error_time_stamp.html",errors="the stop date is after 2018-03-27")

        pars['features'] = request.form.getlist('features')

        df = get_data(pars)

        plot = make_plot(df, pars)

        script, div = components(plot)

        return render_template("graph.html", symbol=pars['symbl'], the_div=div, the_script=script)


#===========================================================================================
def get_data(pars):
    query_url = 'https://www.quandl.com/api/v3/datatables/WIKI/PRICES'
    quandl_api_key = os.environ.get('QUANDL_API_KEY')
    stock_name = pars['symbl']

    start = pars['start'] #datetime.datetime.now()
    stop = pars['stop'] #end + dateutil.relativedelta.relativedelta(months=-12)

    date_label = ""
    inc_date = start
    while inc_date <= stop:
        date_label += '{:%Y-%m-%d},'.format(inc_date)
        inc_date += timedelta(1)

    payload = {'ticker':stock_name, 'date':date_label[:-1], 'api_key':quandl_api_key}
    r = requests.get(query_url, params=payload)
    data = r.json()

    colnames = [item['name'] for item in data['datatable']['columns']]
    df = pd.DataFrame(data['datatable']['data'], columns=colnames)#.set_index())
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    return df

#===========================================================================================
def make_plot(df, pars):
    features = pars['features']
    stock_name = pars['symbl']

    source = ColumnDataSource(data={
        'date'    : df['date'],
        'adj_open'    : df.adj_open,
        'adj_close'   : df.adj_close,
        'open'        : df.open,
        'close'       : df.close,
        'volume'      : df.adj_volume
    })


    hover = HoverTool(tooltips=[('Price', '@close')])

    p = figure(title='Quandl WIKI Stock Price for '+stock_name, 
               x_axis_label='Date', x_axis_type='datetime',
               y_axis_label=r'Price ($)',
               plot_height=400, plot_width=700,
               tools=[hover]
              )

    if not features:
        p.circle('date', 'close', size=3, alpha=0.8, source=source, color='blue')
        p.line('date', 'close', source=source, color='blue', legend='Closing price')
    
    if 'open' in features:
        p.circle('date', 'open', size=3, alpha=0.8, source=source, color='red')
        p.line('date', 'open', source=source, color='red', legend='Opening price')

    if 'close' in features:
        p.circle('date', 'close', size=3, alpha=0.8, source=source, color='blue')
        p.line('date', 'close', source=source, color='blue', legend='Closing price')

    if 'adj_opn' in features:
        p.circle('date', 'adj_open', size=3, alpha=0.8, source=source, color='black')
        p.line('date', 'adj_open', source=source, color='black', legend='Adjusted opening price')

    if 'adj_clos' in features:
        p.circle('date', 'adj_close', size=3, alpha=0.8, source=source, color='green')
        p.line('date', 'adj_close', source=source, color='green', legend='Adjusted closing price')

    p.legend.location = 'top_left'

    return p

#===========================================================================================
@app.route('/about')
def about():
  return render_template('about.html')

#===========================================================================================
if __name__ == '__main__':
  app.run(host='0.0.0.0',port=33507, debug=True)
