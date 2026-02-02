import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import qrcode
from io import BytesIO

def checkout_qrcode(df, conn, save_data):     

    # --- 介面導航 ---
    st.set_page_config(page_title="Logistic Community Sharing點名管理系統", layout="wide",initial_sidebar_state="collapsed")

    st.title("🎓 自主簽退")
    with st.form("checkin", clear_on_submit=True):
        name = st.text_input("輸入您的信箱")
        btn = st.form_submit_button("送出")
        if btn:
            if name in df['信箱'].values:
                idx = df[df['信箱'].str.lower() == name].index[0]  
                now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")            
                if pd.isna(df.at[idx, '簽退時間']) and pd.notnull(df.at[idx, '簽到時間']):
                    df.at[idx, '簽退時間'] = now
                    st.info(f"{name} 簽退成功！")
                    save_data(df)
                elif pd.isna(df.at[idx, '簽到時間']):
                    st.info(f"{name} 未簽到，無法簽退")
                else:
                    st.info(f"{name} 已簽退，不需重複簽退") 
            else:
                st.error("名單中無此信箱")

def checkin_on_qrcode(df, conn, save_data):     

    # --- 介面導航 ---
    st.set_page_config(page_title="Logistic Community Sharing點名管理系統", layout="wide")

    st.title("🎓 線上自主簽到")
    with st.form("checkin", clear_on_submit=True):
        name = st.text_input("輸入您的信箱")
        btn = st.form_submit_button("送出")
        if btn:
            if name in df['信箱'].values:
                idx = df[df['信箱'].str.lower() == name].index[0]
                now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
                if pd.isna(df.at[idx, '簽到時間']):
                    df.at[idx, '簽到時間'] = now
                    df.at[idx, 'Mode']="ONLINE"
                    st.info(f"{name} 線上簽到成功！")
                    save_data(df)
                else:
                    st.info(f"{name} 已簽到，不需重複簽到") 
            else:
                st.error("名單中無此信箱")

def checkin_off_qrcode(df, conn, save_data):   

    # --- 介面導航 ---
    st.set_page_config(page_title="Logistic Community Sharing點名管理系統", layout="wide")

    st.title("🎓 現場自主簽到")
    with st.form("checkin", clear_on_submit=True):
        name = st.text_input("輸入您的信箱")
        btn = st.form_submit_button("送出")
        if btn:
            if name in df['信箱'].values:
                idx = df[df['信箱'].str.lower() == name].index[0]
                now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
                if pd.isna(df.at[idx, '簽到時間']):
                    df.at[idx, 'Mode']="ONLINE"
                    df.at[idx, '簽到時間'] = now
                    st.info(f"{name} 現場簽到成功！")
                    save_data(df)
                else:
                    st.info(f"{name} 已簽到，不需重複簽到") 
            else:
                st.error("名單中無此信箱")