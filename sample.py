# Streamlit を st としてimport
import streamlit as st
# タイトルを作成
st.title("Webアプリ開発")
# 見出しを表示
st.write("# 折れ線フラフ")
# 表示するデータをリストで用意
a = [1, 5, 2, 4, 10]
st.line_chart(a)