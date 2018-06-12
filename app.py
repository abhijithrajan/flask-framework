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

app = Flask(__name__)
app.vars = {}


@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        app.vars['symbl'] = request.form['ticker']
        try:
            app.vars['start'] = datetime.strptime(request.form['start'], "%Y-%m-%d")
        except:
            return render_template("error_time_stamp.html",errors="wrong datetime format")
        try:
            app.vars['stop'] = datetime.strptime(request.form['stop'], "%Y-%m-%d")
        except:
            return render_template("error_time_stamp.html",errors="the wrong datetime format")
        if app.vars['start'] >= app.vars['stop']:
            return render_template("error_time_stamp.html",errors="the start date is great than the stop date")
        if app.vars['stop'] > datetime(2018,3,27):
            return render_template("error_time_stamp.html",errors="the stop date is after 2018-03-27")

        app.vars['features'] = request.form.getlist('features')
        return redirect('/plot')

@app.route('/plot')
def make_plot():
    query_url = 'https://www.quandl.com/api/v3/datatables/WIKI/PRICES?'
    quandl_api_key = os.environ.get('QUANDL_API_KEY')
    stock_name = app.vars['symbl']

    start = app.vars['start'] #datetime.datetime.now()
    stop = app.vars['stop'] #end + dateutil.relativedelta.relativedelta(months=-12)

    print('{:%Y-%m-%d},'.format(start) , '{:%Y-%m-%d},'.format(stop), '{:%Y-%m-%d},'.format(start+timedelta(1)))


    date_label = ""
    inc_date = start
    while inc_date <= stop:
        print('{:%Y-%m-%d},'.format(inc_date))
        date_label += '{:%Y-%m-%d},'.format(inc_date)
        inc_date += timedelta(1)

    query = "{}ticker={}&date={}&api_key={}".format(query_url,stock_name,date_label[:-1],quandl_api_key)

    print(query)

    r = requests.get(query)
    data = r.json()

    colnames = [item['name'] for item in data['datatable']['columns']]
    df = pd.DataFrame(data['datatable']['data'], columns=colnames)#.set_index())
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    source = ColumnDataSource(data={
        'date'    : df['date'],
        'adj_open'    : df.adj_open,
        'adj_close'   : df.adj_close,
        'open'        : df.open,
        'close'       : df.close,
        'volume'      : df.adj_volume
    })


    hover = HoverTool(tooltips=[('Price', '@close')
                               ])

    p = figure(title='Quandl WIKI Stock Price for '+stock_name, 
               x_axis_label='Date', x_axis_type='datetime',
               y_axis_label=r'Price ($)',
               plot_height=400, plot_width=700,
               tools=[hover]
              )

    if app.vars['features'] == []:
        p.circle('date', 'close', size=3, alpha=0.8, source=source, color='blue')
        p.line('date', 'close', source=source, color='blue', legend='Closing price')
    
    if 'open' in app.vars['features']:
        p.circle('date', 'open', size=3, alpha=0.8, source=source, color='red')
        p.line('date', 'open', source=source, color='red', legend='Opening price')

    if 'close' in app.vars['features']:
        p.circle('date', 'close', size=3, alpha=0.8, source=source, color='blue')
        p.line('date', 'close', source=source, color='blue', legend='Closing price')

    if 'adj_opn' in app.vars['features']:
        p.circle('date', 'adj_open', size=3, alpha=0.8, source=source, color='black')
        p.line('date', 'adj_open', source=source, color='black', legend='Adjusted opening price')

    if 'adj_clos' in app.vars['features']:
        p.circle('date', 'adj_close', size=3, alpha=0.8, source=source, color='green')
        p.line('date', 'adj_close', source=source, color='green', legend='Adjusted closing price')

    p.legend.location = 'top_left'

    script, div = components(p)

    return render_template("graph.html", the_div=div, the_script=script)

@app.route('/about')
def about():
  return render_template('about.html')


if __name__ == '__main__':
  app.run(host='0.0.0.0',port=33507, debug=True)
