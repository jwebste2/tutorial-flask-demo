from flask import Flask, render_template, request, redirect

import pandas as pd
import numpy as np

# Bokeh nonsense for making interactive plots
# Can reduce this list once I have finalized code
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
from bokeh.models.widgets import CheckboxButtonGroup, RadioButtonGroup
from bokeh.models import CustomJS, Legend, ColumnDataSource, HoverTool

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
    return render_template( 'index.html' ,
                              js_resources='' ,
                              css_resources='' ,
                              plot_script='' ,
                              checkbox_div='<p>Plot will show up here!</p>' ,
                              radiobox_div='' ,
                              plot_div='' )

  if request.method == 'POST':
    # Read user input, prepare to generate a plot
    app.ticker_symbol = request.form['ticker_symbol']

    app.req_url = 'https://www.quandl.com/api/v3/datasets/WIKI/%s/data.json?api_key=%s&rows=350' % \
                  (app.ticker_symbol,app.req_api_key)

    print app.req_url
    
    req = requests.get( app.req_url )
    #req = requests.get( 'https://www.quandl.com/api/v1/datasets/WIKI/%s.json' % (app.vars['ticker_symbol']) , headers={'api_key':'LxcNobipC2ybk8P_Knc-'} )

    # Check that Quandl responded with something rational
    if not( req.status_code == requests.codes.ok ):
      return render_template( 'index.html' ,
                              js_resources='' ,
                              css_resources='' ,
                              plot_script='' ,
                              checkbox_div='<h4>Oops! Your request returned with status code = %s.</h4>'%(req.status_code) ,
                              radiobox_div='<p>This usually means the ticker symbol is not in the data.</p>' ,
                              plot_div='' )

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
    df['Datetime'] = pd.to_datetime( df['Date'] )
    df['Close visible'] = True
    df['Adj. Close alpha'] = 0.8
    df['High alpha'] = 0.8
    df['Low alpha'] = 0.8
    
    # Sweet, now lets do some bokeh magic to make a pretty plot

    # Set the source data
    source = ColumnDataSource( df )
    
    # Initialize hover settings
    hover = HoverTool(tooltips=[
      ("Date", "@Date"),
      ("Close", "@Close"),
    ])
    
    # Create the figure
    fig = figure( width=800 , height=400 , x_axis_type='datetime' , tools=[hover] ,
                  title='TickerPlot::%s'%(app.ticker_symbol) , 
                  x_axis_label='Date' ,
                  y_axis_label='Price' )
    
    # Want to make sure we only plot dates specified by user
    deltaT = pd.Timedelta( days=30 )
    df_mini = df.ix[ df['Datetime'] > pd.to_datetime('today') - deltaT ]

    #controls = [checkbox, radiobox]
    #for control in controls:
    #  control.on_change('value', lambda attr, old, new: update())
    # checkbox.on_change( 'active' , lambda attr, old, new: print(new) )
    
    #fig.line( x='Datetime' , y='Close' , source=source , line_width=2 , color=colors['Blue'] , line_dash='solid' , legend='Close Pr.' , line_alpha='Close alpha' )
    #fig.line( x='Datetime' , y='Adj. Close' , source=source , line_width=2 , color=colors['Red'] , line_dash='dashed' , legend='Adj. Close Pr.' , line_alpha='Adj. Close alpha' )
    #fig.line( x='Datetime' , y='High' , source=source , line_width=2 , color=colors['Green'] , line_dash='dashed' , legend='Day High' , line_alpha='High alpha' )
    #fig.line( x='Datetime' , y='Low' , source=source , line_width=2 , color=colors['Black'] , line_dash='dashed' , legend='Day Low' , line_alpha='Low alpha' )
    line_close = fig.line( x='Datetime' , y='Close' , source=source , line_width=1 , color=colors['Blue'] , line_dash='solid' , legend='Close Pr.' , line_alpha=0.8 )
    line_adjclose = fig.line( x='Datetime' , y='Adj. Close' , source=source , line_width=1 , color=colors['Red'] , line_dash='solid' , legend='Adj. Close Pr.' , line_alpha=0.8 )
    line_high = fig.line( x='Datetime' , y='High' , source=source , line_width=1 , color=colors['Green'] , line_dash='solid' , legend='Day High' , line_alpha=0.8 )
    line_low = fig.line( x='Datetime' , y='Low' , source=source , line_width=1 , color=colors['Black'] , line_dash='solid' , legend='Day Low' , line_alpha=0.8 )
    fig.legend.location = 'top_left'
    fig.legend.orientation = 'horizontal'

    # Create some widgets
    callback_checkbox = CustomJS( args=dict(line_close=line_close, line_adjclose=line_adjclose, line_high=line_high, line_low=line_low) , code="""
      line_close.visible = false;
      line_adjclose.visible = false;
      line_high.visible = false;
      line_low.visible = false;
      for (i in cb_obj.active) {
        if (cb_obj.active[i] == 0) {
            line_close.visible = true;
        } else if (cb_obj.active[i] == 1) {
            line_adjclose.visible = true;
        } else if (cb_obj.active[i] == 2) {
            line_high.visible = true;
        } else if (cb_obj.active[i] == 3) {
            line_low.visible = true;
        }
      }
    """)


    callback_radiobox = CustomJS( args=dict(source=source) , code="""
      data = source.get('data')
      f = cb_obj.get('value')
      
    """)
    
    checkbox = CheckboxButtonGroup( labels=['Close','Adj. Close','High','Low'] , active=[0,1,2,3] , callback=callback_checkbox )
    radiobox = RadioButtonGroup( labels=['1 Month','3 Months','6 Months','1 Year'] , active=0 , callback=callback_radiobox )

    script, div = components( {'checkbox_div':checkbox, 'radiobox_div':radiobox, 'plot_div':fig} )

    return render_template( 'index.html' , plot_label=app.ticker_symbol ,
                            js_resources=INLINE.render_js() ,
                            css_resources=INLINE.render_css() ,
                            plot_script=script ,
                            plot_div=div['plot_div'] ,
                            checkbox_div=div['checkbox_div'] ,
                            radiobox_div=div['radiobox_div'] )

  else:
    return "Method not understood: %s" % (request.method)


if __name__ == '__main__':
  app.run(debug=True)
  app.run(port=33507)
