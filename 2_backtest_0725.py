# coding:utf-8
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
#datas=pd.read_excel('WTIdatainput_0725.xlsx')
datas=pd.read_excel('WTIdatainput_0725_2.xlsx')
def Strategy(datas,win_long, win_short, lossratio=999):
    datas = datas.copy()
    datas['lma'] = datas.CLOSE.rolling(win_long, min_periods=0).mean()
    datas['sma'] = datas.CLOSE.rolling(win_short, min_periods=0).mean()
    datas['position'] = 0  # 记录持仓
    datas['flag'] = 0  # 记录买卖
    pricein = []
    priceout = []
    for i in range(max(1, win_long), datas.shape[0] - 1):
        if  (datas.signal4[i]==1):
            datas.loc[i, 'flag'] = 1
            datas.loc[i + 1, 'position'] = 1
            date_in = datas.date[i]
            datas.loc[i, 'CLOSE'] =  datas.loc[i, 'CLOSE']*1.0002
            price_in = datas.loc[i, 'CLOSE']
            pricein.append([date_in, price_in])
            """
        elif  (datas.sma[i - 1] < datas.lma[i - 1]) & (datas.sma[i] > datas.lma[i]) & (datas.position[i] == 0):
            datas.loc[i, 'flag'] = 1
            datas.loc[i + 1, 'position'] = 1
            date_in = datas.date[i]
            datas.loc[i, 'CLOSE'] =  datas.loc[i, 'CLOSE']*1.0002
            price_in = datas.loc[i, 'CLOSE']
            pricein.append([date_in, price_in])
            
        elif (datas.position[i] == 1) & (datas.CLOSE[i] / price_in - 1 < -lossratio):
            datas.loc[i + 1, 'position'] = 0
            datas.loc[i, 'CLOSE'] =  datas.loc[i, 'CLOSE']*0.9998
            priceout.append([datas.date[i], datas.loc[i, 'CLOSE']])
                    # 当前持仓，死叉，平仓
        elif (datas.sma[i - 1] > datas.lma[i - 1]) & (datas.sma[i] < datas.lma[i]) & (datas.position[i] == 1):
            datas.loc[i, 'flag'] = -1
            datas.loc[i + 1, 'position'] = 0
            datas.loc[i, 'CLOSE'] = datas.loc[i, 'CLOSE'] * 0.9998
            priceout.append([datas.date[i], datas.loc[i, 'CLOSE']])
        """
        elif datas.loc[i, 'signal4'] == 0:
            datas.loc[i + 1, 'position'] = 0
            datas.loc[i, 'CLOSE'] =  datas.loc[i, 'CLOSE']*0.9998
            priceout.append([datas.date[i], datas.loc[i, 'CLOSE']])

    # 其他情况，保持之前仓位不变
        else:
            datas.loc[i + 1, 'position'] = datas.loc[i, 'position']
    p1 = pd.DataFrame(pricein, columns=['datebuy', 'pricebuy'])
    p2 = pd.DataFrame(priceout, columns=['datesell', 'pricesell'])
    transactions = pd.concat([p1, p2], axis=1)
    datas['ret'] = datas.CLOSE.pct_change(1).fillna(0)
    datas['nav'] = (1 + datas.ret * datas.position).cumprod()
    datas['benchmark'] = datas.CLOSE / datas.CLOSE[0]
    stats, result_peryear = performace(transactions, datas)
    return stats, result_peryear, transactions, datas
def performace(transactions,strategy):
    #N = 250
    N =12
    rety = strategy.nav[strategy.shape[0] - 1] ** (N / strategy.shape[0]) - 1
    Sharp = (strategy.ret * strategy.position).mean() / (strategy.ret * strategy.position).std() * np.sqrt(N)
    VictoryRatio = ((transactions.pricesell - transactions.pricebuy) > 0).mean()
    DD = 1 - strategy.nav / strategy.nav.cummax()
    MDD = max(DD)
    # 策略表现
    strategy['year'] = strategy.date
    nav_peryear = strategy.nav.groupby(strategy.year).last() / strategy.nav.groupby(strategy.year).first() - 1
    benchmark_peryear = strategy.benchmark.groupby(strategy.year).last() / strategy.benchmark.groupby(
        strategy.year).first() - 1
    excess_ret = nav_peryear - benchmark_peryear
    result_peryear = pd.concat([nav_peryear, benchmark_peryear, excess_ret], axis=1)
    result_peryear.columns = ['strategy_ret', 'bench_ret', 'excess_ret']
    result_peryear = result_peryear.T
    # 作图
    xtick = np.round(np.linspace(0, strategy.shape[0] - 1, 7), 0)
    xticklabel = strategy.date[xtick]
    plt.figure(figsize=(9, 4))
    ax1 = plt.axes()
    plt.plot(np.arange(strategy.shape[0]), strategy.benchmark, 'black', label='benchmark', linewidth=2)
    plt.plot(np.arange(strategy.shape[0]), strategy.nav, 'red', label='nav', linewidth=2)
    plt.plot(np.arange(strategy.shape[0]), strategy.nav / strategy.benchmark, 'orange', label='RS', linewidth=2)
    plt.legend()
    ax1.set_xticks(xtick)
    ax1.set_xticklabels(xticklabel)
    maxloss = min(transactions.pricesell / transactions.pricebuy - 1)
    plt.show()
    print('------------------------------')
    print('夏普比为:', round(Sharp, 2))
    print('年化收益率为:{}%'.format(round(rety * 100, 2)))
    print('胜率为：{}%'.format(round(VictoryRatio * 100, 2)))
    print('最大回撤率为：{}%'.format(round(MDD * 100, 2)))
    print('单次最大亏损为:{}%'.format(round(-maxloss * 100, 2)))
    print('月均交易次数为：{}(买卖合计)'.format(round(strategy.signal8.abs().sum() / strategy.shape[0] * 20, 2)))
    result = {'Sharp': Sharp,
              'RetYearly': rety,
              'WinRate': VictoryRatio,
              'MDD': MDD,
              'maxlossOnce': -maxloss,
              'num': round(strategy.signal8.abs().sum() / strategy.shape[0], 1)}
    result = pd.DataFrame.from_dict(result, orient='index').T
    return result, result_peryear
Strategy(datas,12,5,0)
"""
signal1
------------------------------
夏普比为: 0.41
年化收益率为:4.22%
胜率为：7.41%
最大回撤率为：14.14%
单次最大亏损为:44.67%
signal2
------------------------------
夏普比为: 0.05
年化收益率为:-1.42%
胜率为：61.54%
最大回撤率为：65.0%
单次最大亏损为:53.16%
月均交易次数为：10.37(买卖合计)
signal3
------------------------------
夏普比为: 0.16
年化收益率为:1.19%
胜率为：31.03%
最大回撤率为：26.55%
单次最大亏损为:47.5%
月均交易次数为：6.31(买卖合计)
signal4
------------------------------
夏普比为: 0.07
年化收益率为:-2.03%
胜率为：7.69%
最大回撤率为：83.6%
单次最大亏损为:35.1%
月均交易次数为：5.99(买卖合计)
signal5
------------------------------
夏普比为: 0.07
年化收益率为:-2.03%
胜率为：7.69%
最大回撤率为：83.6%
单次最大亏损为:35.1%
月均交易次数为：5.78(买卖合计)
signal6
------------------------------
夏普比为: 0.07
年化收益率为:-2.03%
胜率为：7.69%
最大回撤率为：83.6%
单次最大亏损为:35.1%
月均交易次数为：3.74(买卖合计)
signal7
------------------------------
夏普比为: 0.07
年化收益率为:-2.03%
胜率为：7.69%
最大回撤率为：83.6%
单次最大亏损为:35.1%
月均交易次数为：4.17(买卖合计)
signal8
------------------------------
夏普比为: 0.07
年化收益率为:-2.03%
胜率为：7.69%
最大回撤率为：83.6%
单次最大亏损为:35.1%
月均交易次数为：4.17(买卖合计)
"""