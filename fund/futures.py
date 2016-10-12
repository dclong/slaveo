# coding=utf8
"""
计算各类账户的净值
"""
import datetime

import pandas as pd
import numpy as np


# from .nav import Nav


class Futures(object):
    """
    期货账户净值计算
    """

    def __init__(self, df):
        self.df = df.sort_values("datetime")  # 原始数据
        if "tradeDay" not in self.df.columns:
            self.df["tradeDay"] = self.df.datetime.apply(self.get_tradeday)

    def nav_d(self, col="balance", start=None, origin=0):
        """
        日计算净值
        :param col: 要统计的字段,比如 balance:净值 , margin: 保证金
        :param start: 开始时间, 具体到分钟,任意格式
        :param begin: 从什么时候开始显示
        :param origin: 初始值,比如总资金100w,但实际只投入10w,那么就要将origin设为10w
        :return:
        """
        start = pd.to_datetime(start) if start else self.df.datetime.min()
        df = self.df[self.df.datetime >= start].reset_index()

        first = df.loc[0, col]  # 初始资产

        # 生成周期
        nav_se = df.set_index("tradeDay")[col].resample(
            "1T",
            closed="left",
            label="left"
        ).last().dropna().sort_index()

        # 日净值计算
        delta = first - origin
        nav_se -= delta

        # 将净值设为1
        nav_se /= origin
        first_day = nav_se.index.min()
        first_day -= datetime.timedelta(days=1)
        nav_se[first_day] = 1
        nav_se = nav_se.sort_index()

        return nav_se.apply(lambda x: round(x, 3))

    def nav_m(self, col="balance", start=None, tradeDay=None, origin=0, T=1, t='a'):
        """
        分钟净值,只能显示某一天的数据
        :param col: 要统计的字段,比如 balance:净值 , margin: 保证金
        :param start: 统计数据开始时间, 具体到分钟,任意格式
        :param begin: 从什么时候开始显示
        :param origin: 初始值,比如总资金100w,但实际只投入10w,那么就要将origin设为10w
        :param T: 几分钟的周期, 应当能被 60 * 24 整除
        :param t: {'d': 日盘, 'a': 全天}
        :return:
        """
        if 60 * 24 % T != 0:
            raise ValueError(u"60 * 24 % T != 0")

        # 统计数据开始的时间
        if start:
            start = pd.to_datetime(start)
        else:
            start = self.df.datetime.min()

        # 以这一天为净值开始日期
        df = self.df[self.df.datetime >= start]
        first = df[col].iat[0]  # 初始数值, 不能为0
        # 根据初始值计算偏移
        delta = first - origin

        if tradeDay:
            tradeDay = pd.to_datetime(tradeDay).date()
        else:
            tradeDay = self.df.tradeDay.max().date()

        # 截取要显示的一段
        nav_df = df[df.tradeDay == tradeDay]
        if t == 'd':  # 日盘 only
            beginTime = datetime.datetime.combine(tradeDay, datetime.time(9))
            nav_df = nav_df[beginTime <= nav_df.datetime]
        elif t == 'a':  # 全日
            beginTime = datetime.datetime.combine(tradeDay - datetime.timedelta(days=1), datetime.time(21))
            nav_df = nav_df[beginTime <= nav_df.datetime]

        # 实际资本
        nav_se = nav_df.set_index("datetime")[col] - delta

        # 生成周期
        nav_se = nav_se.resample(
            "%sT" % T,
            closed="right",
            label="right",
        ).last().dropna()

        # 将净值设为1
        nav_se /= nav_se[0]

        # 保留小数
        return nav_se.apply(lambda x: round(x, 3))

    def get_tradeday(self, dt):
        """

        :param dt:
        :return:
        """
        if dt.time() > datetime.time(20):
            return pd.to_datetime(dt.date())
        else:
            return pd.to_datetime(dt.date() + datetime.timedelta(days=1))