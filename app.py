from flask import Flask, render_template, request, redirect

import pandas as pd
import numpy as np

# Bokeh nonsense for making interactive plots
# Can reduce this list once I have finalized code
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.models.widgets import CheckboxGroup

# For loading Quandl data
import requests
import simplejson as json

app = Flask(__name__)

# API key for Quandl = LxcNobipC2ybk8P_Knc-
app.ticker_symbol = None
app.req_api_key   = 'LxcNobipC2ybk8P_Knc-'
app.req_url       = None

# Color definitions for Bokeh plot
colors = {
  'Black': '#000000',
  'Red':   '#FF0000',
  'Green': '#00FF00',
  'Blue':  '#0000FF',
}

@app.route('/')
def main():
  return redirect('/index')

@app.route('/index',methods=['GET','POST'])
def index():

  if request.method == 'GET':
    # Render page asking for user input
    return render_template( 'index.html' , plot_div='' , js_resources='' , css_resources='' , plot_script='' )

  if request.method == 'POST':
    # Read user input, prepare to generate a plot
    app.ticker_symbol = request.form['ticker_symbol']

    app.req_url = 'https://www.quandl.com/api/v3/datasets/WIKI/%s/data.json?api_key=%s&rows=30' % \
                  (app.ticker_symbol,app.req_api_key)

    print app.req_url
    
    req = requests.get( app.req_url )
    #req = requests.get( 'https://www.quandl.com/api/v1/datasets/WIKI/%s.json' % (app.vars['ticker_symbol']) , headers={'api_key':'LxcNobipC2ybk8P_Knc-'} )

    # Check that Quandl responded with something rational
    if not( req.status_code == requests.codes.ok ):
      return render_template( 'index.html' ,
                              plot_div='<p>Oops! Your request returned with status code = %s. This usually means the ticker symbol is not in the data.</p>'%(req.status_code) ,
                              js_resources='' ,
                              css_resources='' ,
                              plot_script='' )

    #
    # .json() returns a dict with one 'dataset_data' key
    # This points to another dict with the following columns:
    # [u'column_names', u'collapse', u'end_date', u'transform', u'order', u'frequency', u'limit', u'column_index', u'data', u'start_date']
    #
    # The 'column_names' are...
    # ["Date","Open","High","Low","Close","Volume","Ex-Dividend","Split Ratio","Adj. Open","Adj. High","Adj. Low","Adj. Close","Adj. Volume"]
    #

    
    # Request must be good if the above check passed!
    # Put the data into a pandas DataFrame
    df = pd.DataFrame( req.json()['dataset_data']['data'] , columns=req.json()['dataset_data']['column_names'] )

    # Convert 'Date' column into recognizable datetime format
    df['Date'] = pd.to_datetime( df['Date'] )

    # Sweet, now lets do some bokeh magic to make a pretty plot
    fig = figure( width=800 , height=400 , x_axis_type='datetime' ,
                  title='TickerPlot::%s'%(app.ticker_symbol) , 
                  x_axis_label='Date' ,
                  y_axis_label='Price' )

    # FIXME
    # checkbox_group = CheckboxGroup( labels=["Option 1", "Option 2", "Option 3"], active=[0, 1] )
    
    fig.line( df['Date'] , df['Close'] , line_width=2 , color=colors['Blue'] , line_dash='solid' , legend='Close' )
    fig.line( df['Date'] , df['Adj. Close'] , line_width=2 , color=colors['Red'] , line_dash='dashed' , legend='Adj. Close' )

    fig.legend.location = "top_left"
    script, div = components( fig )

    return render_template( 'index.html' , plot_label=app.ticker_symbol ,
                            js_resources=INLINE.render_js() ,
                            css_resources=INLINE.render_css() ,
                            plot_script=script ,
                            plot_div=div )
  
    
  else:
    return "Method not understood: %s" % (request.method)


if __name__ == '__main__':
  app.run(debug=False)
  app.run(port=33507)
