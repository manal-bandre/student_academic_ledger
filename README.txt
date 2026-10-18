# Student Academic & Activity Ledger — Quick Start

## What is included
- `app.py`: Streamlit GUI and SQLite database setup.
- `requirements.txt`: Python packages.
- The database file `student_ledger.db` is created automatically on first run.
- A fictional demo student is inserted automatically. Replace demo records with approved data.

## Run on Windows
1. Install Python 3.11+ from https://www.python.org/downloads/
2. During setup, tick **Add Python to PATH**.
3. Extract this ZIP to a simple folder, e.g. Desktop\student_academic_ledger_project.
4. Open that folder in File Explorer.
5. Click the address bar, type `cmd`, and press Enter.
6. Run:
   ```
   py -m pip install -r requirements.txt
   py -m streamlit run app.py
   ```
   If `py` does not work, use `python` instead.
7. A browser tab should open. If not, copy the local URL shown in Command Prompt (usually http://localhost:8501).
8. Use the tabs to add students, semesters, subject/lab marks, activities, qualifications and gap years.
9. In **Export & Database Guide**, click **Prepare Excel workbook**, then download the Excel workbook.

## Google Sheets
1. Open https://sheets.google.com and create a blank spreadsheet.
2. In Google Sheets choose **File → Import → Upload** and select the exported `.xlsx` file.
3. Choose **Import location: Insert new sheet(s)** or **Replace spreadsheet** if it is a new blank sheet.
4. Click **Share → General access → Anyone with the link → Viewer** (only if your instructor requires public access; do not expose real personal data).
5. Copy the spreadsheet URL for the form.
6. Important: this is a manual export/import, not live two-way synchronization.

## GUI hosted link
The local URL `http://localhost:8501` only works on your computer. It is not a hosted link for your instructor. If a public URL is required, deploy the app to Streamlit Community Cloud using a GitHub repository, or ask your instructor whether a local demo plus screenshots is acceptable. Do not submit localhost as a public link.

## Notes
- All marks are constrained to 0–100.
- SGPA/CGPA are constrained to 0–10.
- Student-linked rows use foreign keys and cascading deletion.
- Duplicate roll numbers and duplicate semester numbers per student are prevented.
- Demo values are fictional and must be replaced or clearly labelled as sample data.
