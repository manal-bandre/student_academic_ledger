import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).with_name("student_ledger.db")
st.set_page_config(page_title="Student Academic & Activity Ledger", page_icon="🎓", layout="wide")

def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT,
            department TEXT NOT NULL DEFAULT 'Engineering',
            admission_year INTEGER CHECK(admission_year IS NULL OR admission_year >= 2000),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS qualifications (
            qualification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            qualification_type TEXT NOT NULL CHECK(qualification_type IN ('SSC','HSC','Diploma','Other')),
            institution TEXT,
            passing_year INTEGER CHECK(passing_year IS NULL OR passing_year >= 1980),
            marks_percent REAL CHECK(marks_percent IS NULL OR (marks_percent >= 0 AND marks_percent <= 100)),
            FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            UNIQUE(student_id, qualification_type)
        );
        CREATE TABLE IF NOT EXISTS gap_years (
            gap_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            start_year INTEGER NOT NULL,
            end_year INTEGER NOT NULL,
            reason TEXT,
            CHECK(end_year >= start_year),
            FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS semesters (
            semester_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            semester_no INTEGER NOT NULL CHECK(semester_no BETWEEN 1 AND 12),
            academic_year TEXT,
            sgpa REAL CHECK(sgpa IS NULL OR (sgpa >= 0 AND sgpa <= 10)),
            cgpa REAL CHECK(cgpa IS NULL OR (cgpa >= 0 AND cgpa <= 10)),
            status TEXT NOT NULL DEFAULT 'Completed' CHECK(status IN ('Completed','In Progress','Gap')),
            FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            UNIQUE(student_id, semester_no)
        );
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_id INTEGER NOT NULL,
            subject_code TEXT,
            subject_name TEXT NOT NULL,
            subject_type TEXT NOT NULL DEFAULT 'Theory' CHECK(subject_type IN ('Theory','Lab','Project','Practical')),
            internal_marks REAL CHECK(internal_marks IS NULL OR (internal_marks >= 0 AND internal_marks <= 100)),
            external_marks REAL CHECK(external_marks IS NULL OR (external_marks >= 0 AND external_marks <= 100)),
            total_marks REAL GENERATED ALWAYS AS (
                CASE WHEN internal_marks IS NULL AND external_marks IS NULL THEN NULL
                ELSE COALESCE(internal_marks,0) + COALESCE(external_marks,0) END
            ) VIRTUAL,
            FOREIGN KEY(semester_id) REFERENCES semesters(semester_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            activity_name TEXT NOT NULL,
            category TEXT NOT NULL CHECK(category IN ('Technical/Co-curricular','Extra-curricular')),
            activity_type TEXT NOT NULL CHECK(activity_type IN ('Seminar - Internal','Seminar - External','Workshop','Competition','Sports','Cultural','Other')),
            activity_date TEXT,
            description TEXT,
            certificate TEXT,
            FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name);
        CREATE INDEX IF NOT EXISTS idx_semesters_student ON semesters(student_id, semester_no);
        CREATE INDEX IF NOT EXISTS idx_activities_student ON activities(student_id);
        """)
        count = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            con.execute("INSERT INTO students(roll_no,full_name,email,department,admission_year) VALUES(?,?,?,?,?)",
                        ("DEMO001","Aarav Sharma","aarav.demo@example.com","Computer Engineering",2023))
            sid = con.execute("SELECT student_id FROM students WHERE roll_no='DEMO001'").fetchone()[0]
            con.execute("INSERT INTO qualifications(student_id,qualification_type,institution,passing_year,marks_percent) VALUES(?,?,?,?,?)",
                        (sid,"SSC","Demo School",2021,82.5))
            con.execute("INSERT INTO qualifications(student_id,qualification_type,institution,passing_year,marks_percent) VALUES(?,?,?,?,?)",
                        (sid,"HSC","Demo Junior College",2023,74.0))
            for sem, sgpa, cgpa, yr in [(1,7.4,7.4,"2023-24"),(2,7.8,7.6,"2023-24"),(3,8.1,7.8,"2024-25")]:
                con.execute("INSERT INTO semesters(student_id,semester_no,academic_year,sgpa,cgpa,status) VALUES(?,?,?,?,?,?)",
                            (sid,sem,yr,sgpa,cgpa,"Completed"))
            semid = con.execute("SELECT semester_id FROM semesters WHERE student_id=? AND semester_no=1",(sid,)).fetchone()[0]
            con.execute("INSERT INTO subjects(semester_id,subject_code,subject_name,subject_type,internal_marks,external_marks) VALUES(?,?,?,?,?,?)",
                        (semid,"DBMS101","Database Fundamentals","Theory",18,65))
            con.execute("INSERT INTO subjects(semester_id,subject_code,subject_name,subject_type,internal_marks,external_marks) VALUES(?,?,?,?,?,?)",
                        (semid,"DBMSL1","SQL Lab","Lab",24,68))
            con.execute("INSERT INTO activities(student_id,activity_name,category,activity_type,activity_date,description) VALUES(?,?,?,?,?,?)",
                        (sid,"Intro to Cloud Computing","Technical/Co-curricular","Seminar - Internal","2024-08-12","Demo record; replace with real data"))
            con.execute("INSERT INTO gap_years(student_id,start_year,end_year,reason) VALUES(?,?,?,?)",
                        (sid,2022,2022,"Demo gap year; remove if not applicable"))

init_db()

def query_df(sql, params=()):
    with connect() as con:
        return pd.read_sql_query(sql, con, params=params)

def exec_sql(sql, params=()):
    with connect() as con:
        con.execute(sql, params)

st.title("🎓 Student Academic & Activity Ledger")
st.caption("DBMS Mini-Project | Demo records are fictional. Replace them with authorised student data.")
tabs = st.tabs(["Dashboard & Search","Students","Semester & Subjects","Activities & Seminars","Qualifications & Gap Years","Export & Database Guide"])

with tabs[0]:
    search = st.text_input("🔎 Search student by name or roll number", placeholder="Type a name or roll number")
    students = query_df("""SELECT student_id,roll_no,full_name,department,admission_year FROM students
                           WHERE full_name LIKE ? OR roll_no LIKE ? ORDER BY full_name""",
                        (f"%{search}%",f"%{search}%"))
    st.dataframe(students, use_container_width=True, hide_index=True)
    if not students.empty:
        options = {f"{r.full_name} ({r.roll_no})": int(r.student_id) for r in students.itertuples()}
        chosen = st.selectbox("Choose student to view", list(options.keys()))
        sid = options[chosen]
        sems = query_df("SELECT semester_no,academic_year,sgpa,cgpa,status FROM semesters WHERE student_id=? ORDER BY semester_no",(sid,))
        gaps = query_df("SELECT start_year,end_year,reason FROM gap_years WHERE student_id=? ORDER BY start_year",(sid,))
        a,b,c = st.columns(3)
        a.metric("Semesters recorded", len(sems))
        b.metric("Activities recorded", int(query_df("SELECT COUNT(*) n FROM activities WHERE student_id=?",(sid,)).iloc[0]["n"]))
        c.metric("Gap periods recorded", len(gaps))
        if not sems.empty:
            st.subheader("Semester Progression Curve")
            chart = sems.set_index("semester_no")[["sgpa","cgpa"]]
            st.line_chart(chart, y=["sgpa","cgpa"])
            st.caption("Gap-year markers (if any): " + ("; ".join(f'{r.start_year}–{r.end_year}' for r in gaps.itertuples()) if not gaps.empty else "No gap year recorded"))
            st.dataframe(sems, use_container_width=True, hide_index=True)
        else:
            st.info("No semester records yet. Add them in the Semester & Subjects tab.")
        subjects = query_df("""SELECT se.semester_no,s.subject_code,s.subject_name,s.subject_type,s.internal_marks,s.external_marks,s.total_marks
                               FROM subjects s JOIN semesters se ON s.semester_id=se.semester_id
                               WHERE se.student_id=? ORDER BY se.semester_no,s.subject_name""",(sid,))
        st.subheader("Subject and Lab Marks")
        st.dataframe(subjects, use_container_width=True, hide_index=True)
        acts = query_df("SELECT activity_name,category,activity_type,activity_date,description FROM activities WHERE student_id=? ORDER BY activity_date DESC",(sid,))
        st.subheader("Portfolio")
        st.dataframe(acts, use_container_width=True, hide_index=True)
    else:
        st.info("No matching students. Add a student in the Students tab.")

with tabs[1]:
    st.subheader("Add student")
    with st.form("add_student", clear_on_submit=True):
        col1,col2 = st.columns(2)
        roll = col1.text_input("Roll number *")
        name = col2.text_input("Full name *")
        email = col1.text_input("Email")
        dept = col2.text_input("Department", value="Engineering")
        year = col1.number_input("Admission year", min_value=2000, max_value=2100, value=2026)
        submitted = st.form_submit_button("Save student")
        if submitted:
            if not roll.strip() or not name.strip():
                st.error("Roll number and full name are required.")
            else:
                try:
                    exec_sql("INSERT INTO students(roll_no,full_name,email,department,admission_year) VALUES(?,?,?,?,?)",
                             (roll.strip(),name.strip(),email.strip() or None,dept.strip() or "Engineering",int(year)))
                    st.success("Student saved.")
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f"Could not save: {e}")
    st.subheader("Current students")
    st.dataframe(query_df("SELECT * FROM students ORDER BY full_name"), use_container_width=True, hide_index=True)
    all_students = query_df("SELECT student_id,roll_no,full_name FROM students ORDER BY full_name")
    if not all_students.empty:
        labels = {f"{r.full_name} ({r.roll_no})":int(r.student_id) for r in all_students.itertuples()}
        delete_choice = st.selectbox("Select student to delete (deletes linked records too)", list(labels.keys()), key="delete_student")
        confirm = st.checkbox("I understand this permanently deletes this student's linked records", key="confirm_delete")
        if st.button("Delete selected student", disabled=not confirm):
            exec_sql("DELETE FROM students WHERE student_id=?", (labels[delete_choice],))
            st.success("Student and linked records deleted.")
            st.rerun()

with tabs[2]:
    st.subheader("Add semester")
    stus = query_df("SELECT student_id,roll_no,full_name FROM students ORDER BY full_name")
    if stus.empty:
        st.info("Add a student first.")
    else:
        slabels = {f"{r.full_name} ({r.roll_no})":int(r.student_id) for r in stus.itertuples()}
        with st.form("add_semester", clear_on_submit=True):
            who = st.selectbox("Student", list(slabels.keys()))
            s_no = st.number_input("Semester number", min_value=1, max_value=12, value=1)
            acad = st.text_input("Academic year", placeholder="2025-26")
            sgpa = st.number_input("SGPA (0–10)", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
            cgpa = st.number_input("CGPA (0–10)", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
            status = st.selectbox("Status", ["Completed","In Progress","Gap"])
            if st.form_submit_button("Save semester"):
                try:
                    exec_sql("INSERT INTO semesters(student_id,semester_no,academic_year,sgpa,cgpa,status) VALUES(?,?,?,?,?,?)",
                             (slabels[who],int(s_no),acad.strip() or None,float(sgpa),float(cgpa),status))
                    st.success("Semester saved.")
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f"Could not save. Semester number must be unique per student. Details: {e}")
        st.divider()
        st.subheader("Add subject / lab marks")
        semdf = query_df("""SELECT se.semester_id,se.semester_no,s.full_name,s.roll_no FROM semesters se
                            JOIN students s ON s.student_id=se.student_id ORDER BY s.full_name,se.semester_no""")
        if not semdf.empty:
            semlabels = {f"{r.full_name} ({r.roll_no}) — Semester {r.semester_no}":int(r.semester_id) for r in semdf.itertuples()}
            with st.form("add_subject", clear_on_submit=True):
                sempick = st.selectbox("Semester record", list(semlabels.keys()))
                code = st.text_input("Subject code")
                subname = st.text_input("Subject name *")
                typ = st.selectbox("Subject type", ["Theory","Lab","Project","Practical"])
                internal = st.number_input("Internal marks (0–100)", min_value=0.0, max_value=100.0, value=0.0)
                external = st.number_input("External marks (0–100)", min_value=0.0, max_value=100.0, value=0.0)
                if st.form_submit_button("Save subject marks"):
                    if not subname.strip():
                        st.error("Subject name is required.")
                    else:
                        exec_sql("INSERT INTO subjects(semester_id,subject_code,subject_name,subject_type,internal_marks,external_marks) VALUES(?,?,?,?,?,?)",
                                 (semlabels[sempick],code.strip() or None,subname.strip(),typ,float(internal),float(external)))
                        st.success("Subject and marks saved.")
                        st.rerun()
        st.subheader("All subject marks")
        st.dataframe(query_df("""SELECT st.full_name,st.roll_no,se.semester_no,s.subject_code,s.subject_name,s.subject_type,
                                 s.internal_marks,s.external_marks,s.total_marks
                                 FROM subjects s JOIN semesters se ON se.semester_id=s.semester_id
                                 JOIN students st ON st.student_id=se.student_id
                                 ORDER BY st.full_name,se.semester_no,s.subject_name"""),
                     use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Add activity or seminar")
    stus = query_df("SELECT student_id,roll_no,full_name FROM students ORDER BY full_name")
    if not stus.empty:
        slabels = {f"{r.full_name} ({r.roll_no})":int(r.student_id) for r in stus.itertuples()}
        with st.form("add_activity", clear_on_submit=True):
            who = st.selectbox("Student", list(slabels.keys()), key="act_student")
            aname = st.text_input("Activity / seminar name *")
            category = st.selectbox("Portfolio category", ["Technical/Co-curricular","Extra-curricular"])
            atype = st.selectbox("Type", ["Seminar - Internal","Seminar - External","Workshop","Competition","Sports","Cultural","Other"])
            adate = st.date_input("Date", value=date.today())
            desc = st.text_area("Description")
            cert = st.text_input("Certificate / evidence link (optional)")
            if st.form_submit_button("Save activity"):
                if not aname.strip():
                    st.error("Activity name is required.")
                else:
                    exec_sql("INSERT INTO activities(student_id,activity_name,category,activity_type,activity_date,description,certificate) VALUES(?,?,?,?,?,?,?)",
                             (slabels[who],aname.strip(),category,atype,adate.isoformat(),desc.strip() or None,cert.strip() or None))
                    st.success("Activity saved.")
                    st.rerun()
    st.divider()
    f1,f2 = st.columns(2)
    cat_filter = f1.selectbox("Filter category", ["All","Technical/Co-curricular","Extra-curricular"])
    sem_filter = f2.selectbox("Filter seminars", ["All","Seminar - Internal","Seminar - External"])
    sql = """SELECT st.full_name,st.roll_no,a.activity_name,a.category,a.activity_type,a.activity_date,a.description,a.certificate
             FROM activities a JOIN students st ON st.student_id=a.student_id WHERE 1=1"""
    params=[]
    if cat_filter != "All":
        sql += " AND a.category=?"; params.append(cat_filter)
    if sem_filter != "All":
        sql += " AND a.activity_type=?"; params.append(sem_filter)
    sql += " ORDER BY a.activity_date DESC"
    st.dataframe(query_df(sql,tuple(params)), use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Qualifications")
    stus = query_df("SELECT student_id,roll_no,full_name FROM students ORDER BY full_name")
    if not stus.empty:
        slabels = {f"{r.full_name} ({r.roll_no})":int(r.student_id) for r in stus.itertuples()}
        with st.form("qualification_form", clear_on_submit=True):
            who = st.selectbox("Student", list(slabels.keys()), key="qual_student")
            qtype = st.selectbox("Qualification", ["SSC","HSC","Diploma","Other"])
            inst = st.text_input("School / college")
            py = st.number_input("Passing year", min_value=1980, max_value=2100, value=2023)
            pct = st.number_input("Percentage (0–100)", min_value=0.0, max_value=100.0, value=0.0)
            if st.form_submit_button("Save qualification"):
                try:
                    exec_sql("INSERT INTO qualifications(student_id,qualification_type,institution,passing_year,marks_percent) VALUES(?,?,?,?,?)",
                             (slabels[who],qtype,inst.strip() or None,int(py),float(pct)))
                    st.success("Qualification saved.")
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f"Only one record per qualification type per student. {e}")
    st.dataframe(query_df("""SELECT st.full_name,st.roll_no,q.qualification_type,q.institution,q.passing_year,q.marks_percent
                             FROM qualifications q JOIN students st ON st.student_id=q.student_id ORDER BY st.full_name,q.passing_year"""),
                 use_container_width=True, hide_index=True)
    st.divider()
    st.subheader("Record a gap / drop year")
    if not stus.empty:
        with st.form("gap_form", clear_on_submit=True):
            who = st.selectbox("Student", list(slabels.keys()), key="gap_student")
            start = st.number_input("Start year", min_value=1980, max_value=2100, value=2024)
            end = st.number_input("End year", min_value=1980, max_value=2100, value=2024)
            reason = st.text_input("Reason (optional)")
            if st.form_submit_button("Save gap year"):
                if end < start:
                    st.error("End year must be greater than or equal to start year.")
                else:
                    exec_sql("INSERT INTO gap_years(student_id,start_year,end_year,reason) VALUES(?,?,?,?)",
                             (slabels[who],int(start),int(end),reason.strip() or None))
                    st.success("Gap year saved.")
                    st.rerun()
    st.dataframe(query_df("""SELECT st.full_name,st.roll_no,g.start_year,g.end_year,g.reason FROM gap_years g
                             JOIN students st ON st.student_id=g.student_id ORDER BY st.full_name,g.start_year"""),
                 use_container_width=True, hide_index=True)

with tabs[5]:
    st.subheader("Export records")
    st.write("Download a workbook containing the main tables. You can import the relevant sheets into Google Sheets.")
    if st.button("Prepare Excel workbook"):
        output = Path(__file__).with_name("student_ledger_export.xlsx")
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            query_df("SELECT * FROM students").to_excel(writer, sheet_name="Students", index=False)
            query_df("SELECT * FROM qualifications").to_excel(writer, sheet_name="Qualifications", index=False)
            query_df("SELECT * FROM semesters").to_excel(writer, sheet_name="Semesters", index=False)
            query_df("""SELECT se.student_id,se.semester_no,s.* FROM subjects s JOIN semesters se ON se.semester_id=s.semester_id""").to_excel(writer, sheet_name="Subjects_Labs", index=False)
            query_df("SELECT * FROM activities").to_excel(writer, sheet_name="Activities", index=False)
            query_df("SELECT * FROM gap_years").to_excel(writer, sheet_name="Gap_Years", index=False)
        st.success("Workbook prepared.")
        st.download_button("⬇️ Download Excel workbook", data=output.read_bytes(),
                           file_name="student_ledger_export.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.subheader("Database rules")
    st.markdown("""
    - **Primary keys** uniquely identify records.
    - **Foreign keys** link records to students/semesters; linked records are deleted when a student is deleted (CASCADE).
    - **UNIQUE** prevents duplicate roll numbers and duplicate semester numbers for the same student.
    - **CHECK constraints** validate marks (0–100), SGPA/CGPA (0–10), qualification percentages (0–100), and allowed category values.
    - **Indexes** support faster name, semester, and activity lookups.
    - **3NF design** separates student profile, qualifications, semesters, subjects, gap years, and activities into related tables.
    """)
    st.warning("Spreadsheet export is a one-time export. This version does not automatically synchronize changes both ways with Google Sheets.")
    st.code("streamlit run app.py", language="bash")
    st.caption("For a clean demo, use fictional data only. Do not upload real student records publicly without permission.")
import streamlit as st
from google_sheets_sync import connect_sheet

if st.button("Test Google Sheets Connection"):
    try:
        sheet = connect_sheet()
        st.success(
            f"Connected to: {sheet.title}"
        )
    except Exception as e:
        st.error(f"Connection failed: {e}")