import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import io
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="GradeFlow | Student Grade Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: #f5f7fb;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #1e293b 100%);
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Login */
    .login-container {
        max-width: 430px;
        margin: 70px auto;
        padding: 35px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 15px 45px rgba(0,0,0,0.10);
    }

    .login-title {
        text-align: center;
        color: #4f46e5;
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .login-subtitle {
        text-align: center;
        color: #64748b;
        margin-bottom: 30px;
    }

    /* Headers */
    .main-title {
        font-size: 38px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #64748b;
        font-size: 16px;
        margin-bottom: 25px;
    }

    /* Cards */
    .metric-card {
        background: white;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 5px 20px rgba(0,0,0,0.04);
        margin-bottom: 15px;
    }

    .metric-title {
        color: #64748b;
        font-size: 14px;
        font-weight: 600;
    }

    .metric-value {
        color: #111827;
        font-size: 30px;
        font-weight: 800;
        margin-top: 5px;
    }

    .metric-icon {
        font-size: 28px;
    }

    /* Student cards */
    .student-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    /* Grade badges */
    .grade-A {
        background: #dcfce7;
        color: #166534;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
    }

    .grade-B {
        background: #dbeafe;
        color: #1d4ed8;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
    }

    .grade-C {
        background: #fef3c7;
        color: #92400e;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
    }

    .grade-D {
        background: #ffedd5;
        color: #c2410c;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
    }

    .grade-F {
        background: #fee2e2;
        color: #b91c1c;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }

    /* Tables */
    .dataframe {
        border-radius: 12px;
    }

    /* Hide Streamlit menu */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "student_grades.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            department TEXT,
            semester TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            marks REAL NOT NULL,
            max_marks REAL DEFAULT 100,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
    """)

    # Default admin account
    username = "admin"
    password = hash_password("admin123")

    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    )

    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# AUTHENTICATION
# =========================================================

def authenticate(username, password):
    conn = get_connection()

    result = conn.execute(
        """
        SELECT * FROM users
        WHERE username = ? AND password = ?
        """,
        (username, hash_password(password))
    ).fetchone()

    conn.close()

    return result is not None


def login_page():

    st.markdown("""
    <div class="login-container">
        <div class="login-title">🎓 GradeFlow</div>
        <div class="login-subtitle">
            Student Grade Management System
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        login = st.form_submit_button(
            "🔐 Login",
            use_container_width=True
        )

        if login:

            if authenticate(username, password):

                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()

            else:
                st.error("❌ Invalid username or password")

    st.info(
        "Demo Login → Username: `admin` | Password: `admin123`"
    )


# =========================================================
# STUDENT FUNCTIONS
# =========================================================

def add_student(student_id, name, email, department, semester):

    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO students
            (student_id, name, email, department, semester, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student_id,
                name,
                email,
                department,
                semester,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def get_students():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM students ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def delete_student(student_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM grades WHERE student_id = ?",
        (student_id,)
    )

    conn.execute(
        "DELETE FROM students WHERE student_id = ?",
        (student_id,)
    )

    conn.commit()
    conn.close()


# =========================================================
# GRADE FUNCTIONS
# =========================================================

def calculate_grade(percentage):

    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


def save_grade(student_id, subject, marks, max_marks):

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT id FROM grades
        WHERE student_id = ? AND subject = ?
        """,
        (student_id, subject)
    ).fetchone()

    if existing:

        conn.execute(
            """
            UPDATE grades
            SET marks = ?, max_marks = ?
            WHERE student_id = ? AND subject = ?
            """,
            (marks, max_marks, student_id, subject)
        )

    else:

        conn.execute(
            """
            INSERT INTO grades
            (student_id, subject, marks, max_marks)
            VALUES (?, ?, ?, ?)
            """,
            (student_id, subject, marks, max_marks)
        )

    conn.commit()
    conn.close()


def get_grades():

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            students.student_id,
            students.name,
            students.department,
            students.semester,
            grades.subject,
            grades.marks,
            grades.max_marks
        FROM grades
        JOIN students
        ON students.student_id = grades.student_id
        """,
        conn
    )

    conn.close()

    return df


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    st.markdown(
        '<div class="main-title">📊 Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Overview of student academic performance</div>',
        unsafe_allow_html=True
    )

    students = get_students()
    grades = get_grades()

    total_students = len(students)

    if len(grades) > 0:

        grades["percentage"] = (
            grades["marks"] /
            grades["max_marks"]
        ) * 100

        average = grades["percentage"].mean()

        pass_rate = (
            (grades["percentage"] >= 50).mean()
            * 100
        )

        highest = grades["percentage"].max()

    else:

        average = 0
        pass_rate = 0
        highest = 0

    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        ("👨‍🎓", "Total Students", total_students),
        ("📈", "Average Score", f"{average:.1f}%"),
        ("✅", "Pass Rate", f"{pass_rate:.1f}%"),
        ("🏆", "Highest Score", f"{highest:.1f}%")
    ]

    for col, (icon, title, value) in zip(
        [col1, col2, col3, col4],
        metrics
    ):

        with col:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    if len(grades) == 0:

        st.info(
            "No grade data available yet. Add students and grades to see analytics."
        )
        return

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📚 Subject Performance")

        subject_avg = (
            grades.groupby("subject")["percentage"]
            .mean()
            .sort_values(ascending=False)
        )

        st.bar_chart(subject_avg)

    with col2:

        st.subheader("🎯 Grade Distribution")

        grades["grade"] = grades["percentage"].apply(
            calculate_grade
        )

        distribution = grades["grade"].value_counts()

        st.bar_chart(distribution)


# =========================================================
# STUDENT MANAGEMENT
# =========================================================

def student_management():

    st.markdown(
        '<div class="main-title">👨‍🎓 Student Management</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Add and manage student records</div>',
        unsafe_allow_html=True
    )

    with st.expander("➕ Add New Student", expanded=True):

        with st.form("student_form"):

            col1, col2 = st.columns(2)

            with col1:

                student_id = st.text_input(
                    "Student ID",
                    placeholder="e.g. STU001"
                )

                name = st.text_input(
                    "Full Name",
                    placeholder="Enter student name"
                )

                email = st.text_input(
                    "Email",
                    placeholder="student@example.com"
                )

            with col2:

                department = st.selectbox(
                    "Department",
                    [
                        "Computer Science",
                        "Information Technology",
                        "Electronics",
                        "Mechanical",
                        "Civil",
                        "Business Administration"
                    ]
                )

                semester = st.selectbox(
                    "Semester",
                    [
                        "Semester 1",
                        "Semester 2",
                        "Semester 3",
                        "Semester 4",
                        "Semester 5",
                        "Semester 6",
                        "Semester 7",
                        "Semester 8"
                    ]
                )

            submitted = st.form_submit_button(
                "Add Student",
                use_container_width=True
            )

            if submitted:

                if not student_id or not name:

                    st.warning(
                        "Please enter Student ID and Name."
                    )

                else:

                    success = add_student(
                        student_id,
                        name,
                        email,
                        department,
                        semester
                    )

                    if success:

                        st.success(
                            f"✅ {name} added successfully!"
                        )

                    else:

                        st.error(
                            "Student ID already exists."
                        )

    st.divider()

    st.subheader("📋 Student Records")

    students = get_students()

    if students.empty:

        st.info("No students have been added yet.")

    else:

        search = st.text_input(
            "🔎 Search students",
            placeholder="Search by ID or name..."
        )

        if search:

            students = students[
                students["student_id"]
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                students["name"]
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        display = students[
            [
                "student_id",
                "name",
                "email",
                "department",
                "semester"
            ]
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("🗑️ Delete Student")

        selected = st.selectbox(
            "Select student",
            students["student_id"].tolist()
        )

        if st.button(
            "Delete Selected Student",
            type="secondary"
        ):

            delete_student(selected)

            st.success(
                "Student deleted successfully."
            )

            st.rerun()


# =========================================================
# GRADE ENTRY
# =========================================================

def grade_entry():

    st.markdown(
        '<div class="main-title">📝 Grade Entry</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Enter and update student marks</div>',
        unsafe_allow_html=True
    )

    students = get_students()

    if students.empty:

        st.warning(
            "Please add students before entering grades."
        )
        return

    student_options = {
        f"{row.student_id} - {row.name}":
        row.student_id
        for row in students.itertuples()
    }

    selected = st.selectbox(
        "Select Student",
        list(student_options.keys())
    )

    student_id = student_options[selected]

    subjects = [
        "Mathematics",
        "English",
        "Science",
        "Computer Science",
        "Programming",
        "Database",
        "Data Structures"
    ]

    subject = st.selectbox(
        "Subject",
        subjects
    )

    col1, col2 = st.columns(2)

    with col1:

        max_marks = st.number_input(
            "Maximum Marks",
            min_value=1.0,
            value=100.0
        )

    with col2:

        marks = st.number_input(
            "Marks Obtained",
            min_value=0.0,
            max_value=float(max_marks),
            value=0.0
        )

    percentage = (
        marks / max_marks * 100
        if max_marks > 0
        else 0
    )

    grade = calculate_grade(percentage)

    st.info(
        f"Score: **{percentage:.1f}%** | Grade: **{grade}**"
    )

    if st.button(
        "💾 Save Grade",
        use_container_width=True
    ):

        save_grade(
            student_id,
            subject,
            marks,
            max_marks
        )

        st.success(
            "Grade saved successfully!"
        )

    st.divider()

    st.subheader("📋 Existing Grades")

    grades = get_grades()

    student_grades = grades[
        grades["student_id"] == student_id
    ]

    if student_grades.empty:

        st.info(
            "No grades entered for this student."
        )

    else:

        student_grades = student_grades.copy()

        student_grades["Percentage"] = (
            student_grades["marks"] /
            student_grades["max_marks"] * 100
        ).round(1)

        student_grades["Grade"] = (
            student_grades["Percentage"]
            .apply(calculate_grade)
        )

        st.dataframe(
            student_grades[
                [
                    "subject",
                    "marks",
                    "max_marks",
                    "Percentage",
                    "Grade"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# LEADERBOARD
# =========================================================

def leaderboard():

    st.markdown(
        '<div class="main-title">🏆 Leaderboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Top performing students</div>',
        unsafe_allow_html=True
    )

    grades = get_grades()

    if grades.empty:

        st.info("No grade data available.")
        return

    summary = (
        grades.groupby(
            ["student_id", "name"]
        )
        .agg(
            total_marks=("marks", "sum"),
            total_max=("max_marks", "sum")
        )
        .reset_index()
    )

    summary["percentage"] = (
        summary["total_marks"] /
        summary["total_max"] * 100
    )

    summary["grade"] = (
        summary["percentage"]
        .apply(calculate_grade)
    )

    summary = summary.sort_values(
        "percentage",
        ascending=False
    ).reset_index(drop=True)

    summary["Rank"] = range(
        1,
        len(summary) + 1
    )

    summary["percentage"] = (
        summary["percentage"].round(2)
    )

    summary = summary[
        [
            "Rank",
            "student_id",
            "name",
            "percentage",
            "grade"
        ]
    ]

    summary.columns = [
        "Rank",
        "Student ID",
        "Student Name",
        "Percentage",
        "Grade"
    ]

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# ANALYTICS
# =========================================================

def analytics():

    st.markdown(
        '<div class="main-title">📈 Analytics</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Detailed academic performance analysis</div>',
        unsafe_allow_html=True
    )

    grades = get_grades()

    if grades.empty:

        st.info("No grade data available.")
        return

    grades["percentage"] = (
        grades["marks"] /
        grades["max_marks"] * 100
    )

    grades["grade"] = (
        grades["percentage"]
        .apply(calculate_grade)
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("📚 Average by Subject")

        subject_avg = (
            grades.groupby("subject")["percentage"]
            .mean()
            .round(2)
        )

        st.bar_chart(subject_avg)

    with col2:

        st.subheader("🎯 Grade Distribution")

        grade_counts = (
            grades["grade"]
            .value_counts()
        )

        st.bar_chart(grade_counts)

    st.divider()

    st.subheader("📊 Score Distribution")

    st.line_chart(
        grades["percentage"]
    )


# =========================================================
# REPORTS
# =========================================================

def reports():

    st.markdown(
        '<div class="main-title">📄 Student Reports</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Generate individual student performance reports</div>',
        unsafe_allow_html=True
    )

    students = get_students()
    grades = get_grades()

    if students.empty:

        st.info("No students available.")
        return

    selected = st.selectbox(
        "Select Student",
        students["student_id"].tolist()
    )

    student = students[
        students["student_id"] == selected
    ].iloc[0]

    student_grades = grades[
        grades["student_id"] == selected
    ].copy()

    st.markdown(
        f"""
        <div class="student-card">
            <h2>🎓 {student['name']}</h2>
            <p><b>Student ID:</b> {student['student_id']}</p>
            <p><b>Department:</b> {student['department']}</p>
            <p><b>Semester:</b> {student['semester']}</p>
            <p><b>Email:</b> {student['email']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if student_grades.empty:

        st.warning(
            "No grades available for this student."
        )
        return

    student_grades["Percentage"] = (
        student_grades["marks"] /
        student_grades["max_marks"] * 100
    )

    student_grades["Grade"] = (
        student_grades["Percentage"]
        .apply(calculate_grade)
    )

    total_marks = student_grades["marks"].sum()
    total_max = student_grades["max_marks"].sum()

    overall_percentage = (
        total_marks / total_max * 100
    )

    overall_grade = calculate_grade(
        overall_percentage
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Marks",
        f"{total_marks:.0f}/{total_max:.0f}"
    )

    col2.metric(
        "Percentage",
        f"{overall_percentage:.2f}%"
    )

    col3.metric(
        "Overall Grade",
        overall_grade
    )

    st.divider()

    report = student_grades[
        [
            "subject",
            "marks",
            "max_marks",
            "Percentage",
            "Grade"
        ]
    ].copy()

    report["Percentage"] = (
        report["Percentage"].round(2)
    )

    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# EXPORT
# =========================================================

def export_data():

    st.markdown(
        '<div class="main-title">💾 Data Export</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Download student and grade data</div>',
        unsafe_allow_html=True
    )

    students = get_students()
    grades = get_grades()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("👨‍🎓 Students")

        csv_students = students.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Students CSV",
            data=csv_students,
            file_name="students.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:

        st.subheader("📚 Grades")

        csv_grades = grades.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Grades CSV",
            data=csv_grades,
            file_name="grades.csv",
            mime="text/csv",
            use_container_width=True
        )


# =========================================================
# MAIN APPLICATION
# =========================================================

initialize_database()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

if not st.session_state.logged_in:

    login_page()

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:15px;
            font-size:30px;
            font-weight:800;
        ">
            🎓 GradeFlow
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        f"Logged in as: {st.session_state.username}"
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "👨‍🎓 Students",
            "📝 Grade Entry",
            "🏆 Leaderboard",
            "📈 Analytics",
            "📄 Reports",
            "💾 Export"
        ]
    )

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()


# =========================================================
# PAGE ROUTING
# =========================================================

if page == "📊 Dashboard":

    dashboard()

elif page == "👨‍🎓 Students":

    student_management()

elif page == "📝 Grade Entry":

    grade_entry()

elif page == "🏆 Leaderboard":

    leaderboard()

elif page == "📈 Analytics":

    analytics()

elif page == "📄 Reports":

    reports()

elif page == "💾 Export":

    export_data()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#94a3b8;
        padding:40px 0 10px 0;
    ">
        🎓 GradeFlow Student Grade Manager
        <br>
        Built with Python + Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
