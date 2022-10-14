from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import tushare as ts
from datetime import datetime # For datetime objects
import pandas as pd
import numpy as np
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
from sqlalchemy import create_engine 

# Import the backtrader platform
import backtrader as bt

#Create a strategy
class TestStrategy(bt.Strategy):


    def log(self, txt, dt=None):
        '''Logging function for this strategy'''
#        dt = dt or self.data[0].datetime.date(0)
#        print('%s, %s' % (dt.isoformat(), txt))
        print('%s, %s' % ('close', txt))


    def __init__(self):
        #Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        print(len(self.datas[0].open))
        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        #Simply log the closing price of the series from the reference
        self.log('Close, %2f' % self.dataclose[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
#            if self.dataclose[0] < self.dataclose[-1]:
            if True:
                    # current close less than previous close

                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy(size=500)

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    #Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    datapath = './test.csv'

    # Create a Data Feed
#    data = bt.feeds.GenericCSVData(
#            dataname=datapath,
#        # Do not pass values before this date
#            fromdate=datetime.datetime(2020, 1, 1),
#        # Do not pass values after this date
#            todate=datetime.datetime(2020, 12, 31),
#            dtformat=('%Y%m%d'),
#            datetime=2,
#            open=3,
#            high=4,
#            low=5,
#            close=6,
#            volume=-1,
#            openinterest=-1
#        )
    start = datetime(2021,1,1)
    end = datetime(2021,10,8)

    engine_ts = create_engine('mysql://root:administrator@127.0.0.1:3306/tushare?charset=utf8&use_unicode=1') ##数据库初始化
    sql='SELECT DISTINCT "000592.sz",trade_date,open,high,low,close FROM Daily ORDER BY trade_date DESC LIMIT 10000;' #构建SQL查询语句
    df=pd.read_sql_query(sql, engine_ts) #运用pandas模块read_sql_query方法执行SQL语句
    df.index = pd.to_datetime(df.trade_date)
    df['openinterest']=0
    dataframe = df[['open','high','low','close','openinterest']]
    print(dataframe)
    input()


    data = bt.feeds.PandasData(dataname=dataframe)
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.05)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
