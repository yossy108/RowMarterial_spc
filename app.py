import math
import streamlit as st
import pandas as pd
import altair as alt

# タイトルを作成
st.title("予想利益シミュレーション")
# サイドバーを作成
st.sidebar.write("## 入力フォーム")

# スライダーの選択値を変数ad_costに代入する
ad_cost = st.sidebar.slider("広告宣伝費（万円）", 1000, 9000)*1.0E+04
fixed_cost = 1000*1.0E+04
cost = ad_cost+fixed_cost

# 広告宣伝費から売上を予想する関数を定義
def calc_earnings(ad_cost):
    earnings = 2.87E+07*math.log(ad_cost)-4.44E+08
    return int(earnings)

# 売上とコストから利益を計算する関数を定義
def calc_profit(earnings, cost):
    profit = earnings-cost
    return int(profit)

earnings = calc_earnings(ad_cost)
profit = calc_profit(earnings, cost)
profit_ratio = int((profit/earnings)*100)

# 広告宣伝費、売上、利益の計算値をリストに格納
data_ad_cost = list(range(1000, 9001, 1))
data_earnings = [calc_earnings(ad_cost*1.0E+04)
                for ad_cost in data_ad_cost]
data_profit = [calc_profit(earnings, ad_cost*1.0E+04+fixed_cost)
              for earnings, ad_cost
              in zip(data_earnings, data_ad_cost)]

max_profit = max(data_profit)
best_ad_cost = data_ad_cost[data_profit.index(max_profit)]

# 3カラムのレイアウト作成
# 3カラムの用意
col1, col2, col3 = st.columns(3)
# col1に指標を表示する
col1.metric("費用", f"{int(cost/1.0E+04)} 万円")
col1.metric("最適な広告投下費用", f"{best_ad_cost} 万円")
# col2に指標を表示する
col2.metric("予想売上", f"{int(earnings/1.0E+04)} 万円")
# col3に指標を表示する
col3.metric("予想利益", f"{int(profit/1.0E+04)} 万円", f"{profit_ratio}%")
col3.metric("予想最大利益", f"{int(max_profit/1.0E+04)} 万円")
# metric([指標名], [指標])

# Altairによるグラフ作成のためのデータフレームを作成
# df_earnings(予想売上)のデータフレームを作成する
# 空のデータフレームを作成
df_earnings = pd.DataFrame()
# ad_costカラムに「広告宣伝費」のリストdata_ad_costを挿入
df_earnings["ad_cost"] = data_ad_cost
# valueカラムに「予想売上のリスト」data_earningsを挿入
df_earnings["value"] = data_earnings
# indicatorカラムに「売上」という文字列を挿入
df_earnings["indicator"] = "売上"

# 同様の流れでdf_profit(予想利益)のデータフレームを作成する
df_profit = pd.DataFrame()
df_profit["ad_cost"] = data_ad_cost
df_profit["value"] = data_profit
df_profit["indicator"] = "利益"

# データフレームの結合（df_earningsとdf_profitを縦に結合）
df = pd.concat([df_earnings, df_profit])
df["value"] = df["value"]/1.0E+04

# Altairによるグラフ設定
chart = alt.Chart(df).mark_line().encode(
    alt.X("ad_cost", title="広告宣伝費（万円）"),
    alt.Y("value", title="売上 & 利益（万円）"),
    color="indicator"
).configure_axis(
    labelFontSize=12,
    titleFontSize=16,
).configure_legend(
    labelFontSize=12,
    titleFontSize=16,
)

# chart=~: グラフの設定をchartに代入
# alt: Altairのライブラリ
# Chart(引数=データフレーム): グラフ作成のクラス
# .mark_line(): 折れ線グラフ
# .encode(): X軸、Y軸、色に関する指定を行う関数
# .congigure_axis(): axis(軸)のcongfigure(設定)
# .congigure_legend(): legend(凡例)のconfigure(設定)

# AltairのグラフをStreamlitに表示
# タイトル追加
st.write("## 広告宣伝費に応じた予測売上・利益の推移")
st.altair_chart(chart, use_container_width=True)

# st.altair_chart(引数=グラフ): グラフを表示するメソッド
# use_container_width=True: グラフの横幅を列の幅に合わせてくれる