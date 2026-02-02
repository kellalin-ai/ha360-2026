import streamlit as st
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
from streamlit_gsheets import GSheetsConnection
import time
import rcs_call_all as rc

# --- 1. 使用 cache_resource 保持連線物件，避免重複建立 ---
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = get_connection()

def load_data():
    # 如果 session_state 裡還沒有資料，或者我們想強制更新
    if 'attendance_data' not in st.session_state:
        # 只在第一次或手動觸發時連接 Google
        st.session_state.attendance_data = conn.read(ttl=0) 
    return st.session_state.attendance_data

def save_data(df):
    # 寫入雲端
    conn.update(data=df)
    # 更新本地暫存，這樣下次 get_data 就會直接拿這份，不用重連
    st.session_state.attendance_data = df
    st.toast("雲端同步完成！")
    st.cache_data.clear() # 強制刷新畫面

def handle_update():
    global df, target, points
    df.loc[df['姓名'] == target, '積分'] += points
    save_data(df)
    st.balloons()
    st.session_state.status_msg = f"✅ 已幫 {target} 增加 {st.session_state.points_to_add} 分"

    # 顯示訊息 (使用 Placeholder 更好)
    if st.session_state.get("status_msg"):
        # 在佔位符中顯示成功訊息
        msg_placeholder.success(st.session_state.status_msg)
        # 讓程式暫停 3 秒，這 3 秒內網頁會維持這個狀態
        time.sleep(3)
        # 重置：清空畫面上的訊息，並清空後台的變數
        msg_placeholder.empty()
        # 將 selectbox 回到第一個選項 (假設第一個選項是空的或預設值)
        st.session_state.target_student = df['姓名'].iloc[0] 
        # 將 number_input 回到預設值 5
        st.session_state.points_to_add = 5
        st.session_state.status_msg = ""

# if not os.path.exists(DB_FILE):
#     df_init = pd.DataFrame([
#         {"信箱": "ZZ0001","姓名":"Apple", "Mode": None,"簽到時間": None, "簽退時間": None, "積分": 0}
#     ])
#     df_init.to_csv(DB_FILE, index=False)
# def load_data():
#     try:
#         # 嘗試用 utf-8-sig 讀取 (最推薦，能處理 Excel 存出的中文)
#         return pd.read_csv(DB_FILE, encoding='utf-8-sig')
#     except UnicodeDecodeError:
#         # 如果還是失敗，嘗試用繁體中文常用的 big5 讀取
#         return pd.read_csv(DB_FILE, encoding='big5')

# def save_data(df):
#     df.to_csv(DB_FILE, index=False)

target = "" 
points = 0

# --- 介面導航 ---
st.set_page_config(page_title="Logistic Community Sharing點名管理系統", layout="wide")
menu = st.sidebar.radio("功能選單", ["目前積分表", "管理員後台"])

# --------------------------
# 頁面 1：學員簽到頁
# --------------------------
mode = st.query_params.get("mode")
if st.session_state.get("attendance_data") is None:
    df = load_data()
    st.session_state.attendance_data = df

if mode == st.secrets["url_modes"]["checkin_on_key"]: #線上checkin
    # 呼叫線上簽到頁面函數
    rc.checkin_on_qrcode(st.session_state.attendance_data, conn, save_data)

elif mode == st.secrets["url_modes"]["checkin_off_key"]: #現場checkin
    # 呼叫簽退頁面函數 
    rc.checkin_off_qrcode(st.session_state.attendance_data, conn, save_data)

elif mode == st.secrets["url_modes"]["checkout_key"]: #checkout
    # 呼叫簽退頁面函數 
    rc.checkout_qrcode(st.session_state.attendance_data, conn, save_data)

elif menu == "目前積分表":
    st.title("🎓 Logistic Community Sharing")
    # 範例：有簽到且有簽退才給予完整出席分
    df['含出席總分'] = df.apply( lambda row:   
        row['積分'] + 20 if ( pd.notnull(row['簽退時間']) and row['Mode']=="OFFLINE" )
        else row['積分'] + 10 if (pd.notnull(row['簽退時間']) and row['Mode']=="ONLINE")
        else row['積分'], axis=1 )
    #依照「積分」進行排序
    # ascending=False 代表「遞減排序」（從大到小）
    df = df.sort_values(by="積分", ascending=False)
    st.dataframe(df, use_container_width=True)

# --------------------------
# 頁面 2：管理員後台
# --------------------------
elif menu == "管理員後台":
    st.title("⚙️ 管理員控制面板")
    # --- 初始化 Session State --- 

    # 密碼驗證
    pwd = st.text_input("請輸入管理員密碼", type="password")
    if pwd == st.secrets["passwords"]["admin_password"]:
        st.success("身分驗證通過")
        #df = load_data()
        # 1. 確保「積分」是整數型態，並把空值補 0
        df['積分'] = pd.to_numeric(df['積分'], errors='coerce').fillna(0).astype(int)
        
        # 2. 確保時間欄位是字串，避免出現 NaN 導致編輯器崩潰
        df['簽到時間'] = df['簽到時間'].fillna("")
        df['簽退時間'] = df['簽退時間'].fillna("")

        # 分成三個控制區塊
        tabs = st.tabs(["🏆 積分管理", 
                        "📝 名單編輯", 
                        "📊 數據導出"])

        with tabs[0]:
            
            st.subheader("互動環節加分")
            col1, col2 = st.columns(2)
            with col1:
                target = st.selectbox("選擇學員", df['姓名'],key="target_student")
            with col2:
                if "points_to_add" not in st.session_state:
                    st.session_state.points_to_add = 5
                points = st.number_input("加分數值", step=1,key="points_to_add")

            msg_placeholder = st.empty()

            st.button("確認加分", on_click=handle_update)

        with tabs[1]:

            st.subheader("手動修改資料")
            # 讓管理員可以直接在網頁上編輯表格
            edited_df = st.data_editor(
                df,
                num_rows="dynamic", # 允許動態增減行數
                column_config={
                    "信箱": st.column_config.TextColumn("信箱", help="請輸入信箱", required=True),
                    "姓名": st.column_config.TextColumn("姓名", help="請輸入全名", required=True),
                    "簽到來自": st.column_config.TextColumn("簽到來自", disabled=True),
                    "簽到時間": st.column_config.TextColumn("簽到時間", disabled=True),
                    "簽退時間": st.column_config.TextColumn("簽退時間", disabled=True),
                    "積分": st.column_config.NumberColumn(
                        "積分",
                        help="預設值為 0",
                        min_value=0,
                        default=0,  # 這行就是你要的預設值！
                        format="%d 分",
                        disabled=True
                    ),
                },
                use_container_width=True
            )



            if st.button("儲存所有修改"):
                save_data(edited_df)
                st.toast("資料庫已更新！")

        with tabs[2]:

            st.subheader("下載統計報表")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8-sig') # utf-8-sig 解決 Excel 亂碼
            st.download_button(
                label="📥 下載為 CSV 檔案",
                data=csv,
                file_name=f"HA360_Report_{datetime.now().date()}.csv",
                mime="text/csv"
            )

    elif pwd != "":
        st.error("密碼錯誤，請重新輸入")