from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

#import tushare as ts
#from datetime import datetime # For datetime objects
import datetime
import pandas as pd
import numpy as np
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
#from sqlalchemy import create_engine 
# Import the backtrader platform
import backtrader as bt
#from matplotlib import plot
import pdb

#Create a strategy
class TestStrategy(bt.Strategy):
    params=(
            ('ma',21),
            ('printlog',False),
            )


    def log(self, txt, dt=None,doprint=False):
        '''Logging function for this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))


    def __init__(self):
        #Keep a reference to the "close" line in the data[0] dataseries
        self.count=0
        self.dataclose = self.datas[0].close
#        print('close[0]:',self.dataclose[0])
#        self.log('Close, %2f' % self.dataclose[0])
        self.dataopen = self.datas[0].open
        self.datetime = self.datas[0].datetime
        self.sma=bt.indicators.SimpleMovingAverage(self.datas[0],period=self.params.ma)
#        self.log('Datetime, %2f' % self.datetime[0])
#        print(self.datas[0])
#        print(self.datas[0].close)
#        print(self.datas[0].open)
#        print(len(self.datas[0].lines))
        # To keep track of pending orders
        self.order = None
#        pdb.set_trace()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, price:%.2f,cost:%.2f,comm:%.2f' %(order.executed.price,order.executed.value,order.executed.comm))
            elif order.issell():
                self.log('SELL EXECUTED, price:%.2f,cost:%.2f,comm:%.2f' %(order.executed.price,order.executed.value,order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None


    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        #Simply log the closing price of the series from the reference
#        print(f'{self.count+1} loop of next')
        self.log('Close, %2f' % self.dataclose[0])
        self.log('Open, %2f' % self.dataopen[0])
        self.log('Datetime, %2f' % self.datetime[0])
        self.log(f'Sma{self.params.ma}, %2f' % self.sma[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
#            if self.dataclose[0] < self.dataclose[-1]:
#            if self.dataclose[0] > self.sma[0]:
#            if True:
#            if self.sma[0]>self.sma[-1]:
            if self.sma[0]>self.sma[-1]:
                if self.sma[-1]<self.sma[-2]:
                    if self.sma[-2]<self.sma[-3]:
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    # current close less than previous close

                # BUY, BUY, BUY!!! (with default parameters)
#                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
#                self.order = self.buy(size=500)
                self.order = self.buy()

        else:

            # Already in the market ... we might sell
#            if len(self) >= (self.bar_executed + 5):
#            if self.sma[0]<self.sma[-1]:
#            if self.dataclose[0]<self.sma[0]:
            if self.dataclose[0]>self.sma[0]*1.2 or self.dataclose[0]<self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
        self.count+=1
#        print('--'*20+'split')


    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.ma, self.broker.getvalue()), doprint=True)

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    #Add a strategy
#    cerebro.addstrategy(TestStrategy)


    #Add a optstrategy
    cerebro.optstrategy(TestStrategy,ma=range(10,30))

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere

    #通过数据库生成CSV文件作为datafeed
    datapath=input('please input the data feed:')
    datapath=datapath.replace('\'','')

    # Create a Data Feed
    data = bt.feeds.GenericCSVData(
            saparator='\t',
            dataname=datapath,
        # Do not pass values before this date
            fromdate=datetime.datetime(2019, 1, 1),
        # Do not pass values after this date
            todate=datetime.datetime(2022, 12, 31),
#            reverse=True,
            dtformat=('%Y%m%d'),
            datetime=1,
            open=2,
            high=3,
            low=4,
            close=5,
            volume=-1,
            openinterest=-1
        )


#    start = datetime(2021,1,1)
#    end = datetime(2021,10,8)

    #直接通过数据库查询来提供datafeed
#    engine_ts = create_engine('mysql://root:administrator@127.0.0.1:3306/tushare?charset=utf8&use_unicode=1') ##数据库初始化
#    sql='SELECT DISTINCT "000592.sz",trade_date,open,high,low,close FROM Daily ORDER BY trade_date DESC LIMIT 10000;' #构建SQL查询语句
#    df=pd.read_sql_query(sql, engine_ts) #运用pandas模块read_sql_query方法执行SQL语句
#    df.index = pd.to_datetime(df.trade_date)
#    df['openinterest']=0
#    dataframe = df[['open','high','low','close','openinterest']]
#    print(dataframe)
#    input()


#    data = bt.feeds.PandasData(dataname=dataframe)
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
#    cerebro.broker.setcommission(commission=0.005)
    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

#    cerebro.plot(volume=False)
