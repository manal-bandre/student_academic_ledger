
import json
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def connect_sheet():
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["google_service_account"]),
        scopes=SCOPES,
    )

    client = gspread.authorize(credentials)

    spreadsheet_id = st.secrets["spreadsheet_id"]
    spreadsheet = client.open_by_key(spreadsheet_id)

    return spreadsheet


def upload_dataframe(df, worksheet_name="StudentRecords"):
    spreadsheet = connect_sheet()

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=max(len(df.columns), 1),
        )

    data = [df.columns.tolist()]
    data += df.fillna("").astype(str).values.tolist()

    worksheet.clear()
    worksheet.update(
        range_name="A1",
        values=data,
    )

    return len(df)


def download_dataframe(worksheet_name="StudentRecords"):
    spreadsheet = connect_sheet()
    worksheet = spreadsheet.worksheet(worksheet_name)

    records = worksheet.get_all_records()
    return pd.DataFrame(records)
