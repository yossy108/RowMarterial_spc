#編集テスト
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import statistics

#初期値 (ファイル読み込み前のエラー防止)
item_list=[]
ins_list=[]
df = pd.DataFrame()

# タイトル
st.title("ABF原料管理図トレンド")

# 解析対象ファイルの読み込みボタン
uploaded_file = st.file_uploader("読み込み用ファイルを選択してください")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='cp932')
    # st.dataframe(df.head())    # 削除
    item_list = sorted(df["品目名称"].unique())
    st.write('ファイルは正常に読み込まれました')

# サイドバーに表示する項目
st.sidebar.write("## 条件指定")
item_selected = st.sidebar.selectbox("品目名称", item_list)
if item_selected is not None:
    # 品目名称で絞り込みした品目にデータフレームを絞り込み
    df = df[df["品目名称"]==item_selected]
    ins_list = sorted(df["検査項目"].unique())
    ins_selected = st.sidebar.selectbox("検査項目", ins_list)

# ULCRの算出式を定義
def calc_UCLCR(data, UCL):
    mean_value = statistics.mean(data)
    std_value = statistics.stdev(data)
    if std_value != 0:
        UCLCR = ((mean_value+3*std_value)-UCL)/std_value
        UCLCR = round(UCLCR,2)
    else: UCLCR = "-"
    return UCLCR

# LCLCRの算出式を定義
def calc_LCLCR(data, LCL):
    mean_value = statistics.mean(data)
    std_value = statistics.stdev(data)
    if std_value != 0:
        LCLCR = (LCL-(mean_value-3*std_value))/std_value
        LCLCR = round(LCLCR,2)
    else: LCLCR = "-"
    return LCLCR

# Cpkの算出式を定義
def calc_Cpk(data, USL, LSL):
    mean_value = statistics.mean(data)
    std_value = statistics.stdev(data)
    if [USL, LSL] == [999999, -99999] or [USL, LSL] == [0, 0]:
        Cpk = "-"
    elif [USL, LSL] != [999999, -99999]:
        Cpk = min((USL-mean_value)/(3*std_value), (mean_value-LSL)/(3*std_value))
    elif USL == 999999:
        Cpk = (mean_value-LSL)/(3*std_value)
    elif LSL == -99999:
        Cpk = (USL-mean_value)/(3*std_value)
    return Cpk

if uploaded_file is not None:

    if ins_selected is not None:
        # 検査項目の絞り込み後、受入日をdatetime型に変換、受入日順に並べ替え
        df = df[df["検査項目"]==ins_selected]
        df["受入日"] = pd.to_datetime(df["受入日"])
        df = df.sort_values(by="受入日", ascending=True)
        # st.dataframe(df.head())    # 削除

        # ロット重複削除（最終受入ロットを残す）
        df = df.drop_duplicates(subset="ロット", keep="last", ignore_index=True)

        # # 規格・管理値設定をしていない場合、nanにreplace。試行したがエラー発生。
        # df["USL"] = df["USL"].replace(999999, "999999")
        # df["LSL"] = df["LSL"].replace(-99999.0, "-99999")
        # df["UCL"] = df["UCL"].replace(999999.0, "999999")
        # df["LCL"] = df["LCL"].replace(-99999.0, "-99999")

        # 現行の管理値、CLCRを計算
        cur_USL = df["USL"].tail(1).iloc[0]
        cur_LSL = df["LSL"].tail(1).iloc[0]
        cur_UCL = df["UCL"].tail(1).iloc[0]
        cur_LCL = df["LCL"].tail(1).iloc[0]
        cur_UCLCR = calc_UCLCR(df["測定値"], cur_UCL)
        cur_LCLCR = calc_LCLCR(df["測定値"], cur_LCL)

        # 現行実績の統計量を計算
        num = len(df["測定値"])
        avg = statistics.mean(df["測定値"])
        std = statistics.stdev(df["測定値"])
        max_value = max(df["測定値"])
        min_value = min(df["測定値"])
        max_value = max(df["測定値"])
        min_value = min(df["測定値"])
        Cpk = calc_Cpk(df["測定値"], cur_USL, cur_LSL)

        # 新しい管理値案、CLCRを計算
        new_UCL = st.sidebar.number_input("UCL案（初期値 = Ave + 3σ）", value = avg+3*std)
        new_LCL = st.sidebar.number_input("LCL案（初期値 = Ave - 3σ）", value = avg-3*std)
        new_UCLCR = calc_UCLCR(df["測定値"], new_UCL)
        new_LCLCR = calc_LCLCR(df["測定値"], new_LCL)

        # 新しい管理値の表示桁数を現行の管理値に合わせる処理（見た目の問題のみ）
        cur_UCL_decimal_count = len(str(cur_UCL).split(".")[1]) if "." in str(cur_UCL) else 0
        formatted_new_UCL = "{:.{}f}".format(new_UCL, cur_UCL_decimal_count)
        cur_LCL_decimal_count = len(str(cur_LCL).split(".")[1]) if "." in str(cur_LCL) else 0
        formatted_new_LCL =  "{:.{}f}".format(new_LCL, cur_LCL_decimal_count)

        # グラフY軸上下限の計算
        # 上下規格設定がない場合は実績最大値 or 新しい管理値の大きい方を取得
        # 上下規格設定がある場合は規格値を取得
        # 現行の±3σ、規格値の最大も含めたいが999999 or -99999を拾ってきてしまうのでこれらを除く処理が一発必要
        if cur_USL == 999999:
            y_axis_upper = max(max_value, new_UCL)
        else:
            y_axis_upper = cur_USL
        
        if cur_LSL == -99999:
            y_axis_lower = min(min_value, new_LCL)
        else:
            y_axis_lower = cur_LSL

        # 新しい管理線をグラフに入れるため、データフレームに追加
        df["new_UCL"] = new_UCL
        df["new_LCL"] = new_LCL

        # グラフ上下限設定の計算が正しくできているかの確認（問題なければ不要）
        df["y_axis_upper"] = y_axis_upper
        df["y_axis_lower"] = y_axis_lower
        
        # Y軸の単位設定
        if not df["単位"].tail(1).empty:
            unit = df["単位"].tail(1).iloc[0]
        else:
            unit = "-"

        # ベース作成（毎回記載すると冗長化するため）
        base = alt.Chart(df).encode(alt.X("ロット:N", title="Lot", sort=None))

        # グラフ作成
        chart = base.mark_line(point=True).encode(
            alt.Y("測定値:Q", title=item_selected + "_" + ins_selected + "   " + f"[{unit}]", scale=alt.Scale(domain=[y_axis_lower, y_axis_upper]))
            )

        # 新旧CL
        cur_UCL_line = base.mark_line(color="green").encode(
            alt.Y("UCL:Q", scale=alt.Scale(domain=[y_axis_lower, y_axis_upper])))
        cur_LCL_line = base.mark_line(color="green").encode(
            alt.Y("LCL:Q", scale=alt.Scale(domain=[y_axis_lower, y_axis_upper])))
        new_UCL_line = base.mark_line(color="red", strokeDash=[2,2]).encode(
            alt.Y("new_UCL:Q", scale=alt.Scale(domain=[y_axis_lower, y_axis_upper])))
        new_LCL_line = base.mark_line(color="red", strokeDash=[2,2]).encode(
            alt.Y("new_LCL:Q", scale=alt.Scale(domain=[y_axis_lower, y_axis_upper])))
        
        st.dataframe(df.tail(5))    # 削除

        # データを重ねる
        layer = alt.layer(chart, cur_UCL_line, cur_LCL_line, new_UCL_line, new_LCL_line)
        # cur_UCL, cur_LCLの表示が必要だが99999など反映しないようY軸設定が必要！

        # タイトル、グラフの表示
        st.write('## トレンドチャート')
        st.altair_chart(layer, use_container_width=True)

        # メトリクスの表示、データ取り込み前の初期値は - としておく
        col1, col2, col3 = st.columns(3)
        if item_selected is None:
            col1.metric('N', '-')
            col1.metric('Average', '-')
            col1.metric('Std.', '-')
            col1.metric("Cpk", "-")
            col2.metric('Current UCL', '-')
            col2.metric('Current LCL', '-')
            col3.metric('New UCL', '-')
            col3.metric('New LCL', '-')
        
        else:
            col1.metric('N', num)
            col1.metric('Average', round(avg,2))
            col1.metric('σ', round(std,2))
            
            # Cpk="-"の場合、"-"とする
            # 現行のUCL/LCLが設定されていない場合、Cpk="-"になるようにdefで定義されている
            if Cpk == "-":
                col1.metric("Cpk", "-")
            else:
                col1.metric("Cpk", round(Cpk, 2))

            # 現行のUCL/LCLが設定されていない項目は"-"とする（計算はされている）
            # UCL=999999, LCL=-99999
            # UCL=0, LCL=0 (例：外観など)
            if cur_UCL == 999999 or cur_UCL == 0:
                col2.metric('Current UCL', "-")
            else:
                col2.metric('Current UCL', cur_UCL)
            
            if cur_LCL == -99999 or cur_LCL == 0:
                col2.metric('Current LCL', "-")
            else:
                col2.metric('Current LCL', cur_LCL)
            
            if cur_UCL == 999999 or cur_UCL == 0:
                col2.metric('Current UCLCR', "-")
            else:
                col2.metric('Current UCLCR', round(cur_UCLCR,1))
                
            if cur_LCL == -99999 or cur_LCL == 0:
                col2.metric('Current LCLCR', "-")
            else:
                col2.metric('Current LCLCR', round(cur_LCLCR,1))
            
            # Average, σともに"0"の項目は"-"とする（計算はされている）
            # UCL=0, LCL=0 (例：外観など)
            if avg == 0 and std == 0:
                col3.metric('New UCL', "-", help="初期値はAve + 3σ")
                col3.metric('New LCL', "-", help="初期値はAve - 3σ")
            else:
                col3.metric('New UCL', formatted_new_UCL, help="初期値はAve + 3σ")
                col3.metric('New LCL', formatted_new_LCL, help="初期値はAve - 3σ")
            
            # 新しいUCLCR/LCLCR="-"、つまりσ=0でCLCRが計算できない場合、"-"とする
            # σ=0の時は、分母が0となるためCLCR="-"となるようにdefで定義している
            if new_UCLCR == "-":
                col3.metric('New UCLCR', "-", help="初期値は0.0")
            else:
                col3.metric('New UCLCR', round(new_UCLCR,1), help="初期値は0.0")
            
            if new_LCLCR == "-":
                col3.metric('New LCLCR', "-", help="初期値は0.0")
            else:
                col3.metric('New LCLCR', round(new_LCLCR,1), help="初期値は0.0")
