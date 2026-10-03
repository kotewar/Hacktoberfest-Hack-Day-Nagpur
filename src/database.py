import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with dictionary row access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the database schema if tables do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Quiz Results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                chapter TEXT,
                total_questions INTEGER,
                score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)
        
        # 3. Topic Mastery table with SM-2 parameters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topic_mastery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic_name TEXT,
                attempts INTEGER DEFAULT 0,
                mastery_percentage REAL DEFAULT 0.0,
                last_practiced TIMESTAMP,
                next_review TIMESTAMP,
                repetitions INTEGER DEFAULT 0,
                interval_days INTEGER DEFAULT 1,
                ease_factor REAL DEFAULT 2.5,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, topic_name)
            );
        """)
        
        # 4. Daily Study Activity table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date DATE DEFAULT CURRENT_DATE,
                minutes_spent INTEGER DEFAULT 0,
                questions_answered INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            );
        """)
        
        # Create a default user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username) VALUES (?);", ("Default Student",))
            
        conn.commit()

# --- User Management ---

def get_all_users() -> List[Dict[str, Any]]:
    """Returns all user profiles."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, created_at FROM users ORDER BY id ASC;")
        return [dict(row) for row in cursor.fetchall()]

def get_or_create_user(username: str) -> Dict[str, Any]:
    """Gets an existing user or creates a new one."""
    username = username.strip()
    if not username:
        username = "Student"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, created_at FROM users WHERE username = ?;", (username,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        cursor.execute("INSERT INTO users (username) VALUES (?);", (username,))
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "username": username, "created_at": datetime.now().isoformat()}

# --- Quiz Results ---

def save_quiz_result(user_id: int, subject: str, chapter: str, total_questions: int, score: float) -> int:
    """Saves a completed quiz result and logs answered questions."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quiz_results (user_id, subject, chapter, total_questions, score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, subject, chapter, total_questions, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        result_id = cursor.lastrowid
        conn.commit()
        
    # Also log study activity
    log_study_activity(user_id, minutes_spent=max(1, total_questions * 2), questions_answered=total_questions)
    return result_id

def get_user_quiz_results(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent quiz submissions for a user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, subject, chapter, total_questions, score, timestamp
            FROM quiz_results
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?;
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]

# --- Spaced Repetition & Topic Mastery ---

def get_topic_mastery(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves mastery records for all practiced topics for a user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, topic_name, attempts, mastery_percentage,
                   last_practiced, next_review, repetitions, interval_days, ease_factor
            FROM topic_mastery
            WHERE user_id = ?
            ORDER BY next_review ASC;
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_topic_mastery_record(user_id: int, topic_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single topic mastery record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, topic_name, attempts, mastery_percentage,
                   last_practiced, next_review, repetitions, interval_days, ease_factor
            FROM topic_mastery
            WHERE user_id = ? AND topic_name = ?;
        """, (user_id, topic_name))
        row = cursor.fetchone()
        return dict(row) if row else None

def save_or_update_topic_mastery(
    user_id: int,
    topic_name: str,
    mastery_percentage: float,
    repetitions: int,
    interval_days: int,
    ease_factor: float,
    next_review: datetime
) -> None:
    """Updates or inserts a topic's SM-2 progress."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    next_review_str = next_review.strftime("%Y-%m-%d %H:%M:%S")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO topic_mastery (
                user_id, topic_name, attempts, mastery_percentage,
                last_practiced, next_review, repetitions, interval_days, ease_factor
            ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, topic_name) DO UPDATE SET
                attempts = attempts + 1,
                mastery_percentage = excluded.mastery_percentage,
                last_practiced = excluded.last_practiced,
                next_review = excluded.next_review,
                repetitions = excluded.repetitions,
                interval_days = excluded.interval_days,
                ease_factor = excluded.ease_factor;
        """, (
            user_id, topic_name, mastery_percentage,
            now_str, next_review_str, repetitions, interval_days, ease_factor
        ))
        conn.commit()

def get_due_reviews(user_id: int) -> List[Dict[str, Any]]:
    """Returns topics whose next_review <= current time."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, topic_name, attempts, mastery_percentage, last_practiced, next_review, interval_days
            FROM topic_mastery
            WHERE user_id = ? AND (next_review <= ? OR next_review IS NULL)
            ORDER BY next_review ASC;
        """, (user_id, now_str))
        return [dict(row) for row in cursor.fetchall()]

# --- Study Logs & Streaks ---

def log_study_activity(user_id: int, minutes_spent: int = 0, questions_answered: int = 0) -> None:
    """Updates or inserts daily study activity for the user."""
    today_str = date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO study_logs (user_id, date, minutes_spent, questions_answered)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                minutes_spent = minutes_spent + excluded.minutes_spent,
                questions_answered = questions_answered + excluded.questions_answered;
        """, (user_id, today_str, minutes_spent, questions_answered))
        conn.commit()

def get_study_streak(user_id: int) -> int:
    """Calculates active daily study streak in days."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date FROM study_logs
            WHERE user_id = ? AND (minutes_spent > 0 OR questions_answered > 0)
            ORDER BY date DESC;
        """, (user_id,))
        rows = cursor.fetchall()
        
    if not rows:
        return 0
        
    dates = {datetime.strptime(row["date"], "%Y-%m-%d").date() for row in rows}
    today = date.today()
    
    # Check if streak is active (studied today or yesterday)
    current_check = today
    if current_check not in dates:
        yesterday = today - timedelta(days=1)
        if yesterday in dates:
            current_check = yesterday
        else:
            return 0
            
    streak = 0
    while current_check in dates:
        streak += 1
        current_check -= timedelta(days=1)
        
    return streak

def get_study_summary(user_id: int) -> Dict[str, Any]:
    """Computes overall statistics: streak, total questions, average accuracy, total time."""
    streak = get_study_streak(user_id)
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Aggregated questions and time from study_logs
        cursor.execute("""
            SELECT COALESCE(SUM(minutes_spent), 0) AS total_minutes,
                   COALESCE(SUM(questions_answered), 0) AS total_questions
            FROM study_logs
            WHERE user_id = ?;
        """, (user_id,))
        log_stats = cursor.fetchone()
        
        # Aggregated quiz score accuracy
        cursor.execute("""
            SELECT COUNT(*) AS total_quizzes,
                   COALESCE(AVG(score / total_questions * 100), 0.0) AS avg_accuracy
            FROM quiz_results
            WHERE user_id = ? AND total_questions > 0;
        """, (user_id,))
        quiz_stats = cursor.fetchone()
        
        return {
            "streak_days": streak,
            "total_minutes": log_stats["total_minutes"] if log_stats else 0,
            "total_questions": log_stats["total_questions"] if log_stats else 0,
            "total_quizzes": quiz_stats["total_quizzes"] if quiz_stats else 0,
            "avg_accuracy": round(quiz_stats["avg_accuracy"] if quiz_stats else 0.0, 1)
        }

def get_daily_study_logs(user_id: int, days: int = 14) -> List[Dict[str, Any]]:
    """Returns daily study activity for the last N days."""
    start_date = (date.today() - timedelta(days=days - 1)).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, minutes_spent, questions_answered
            FROM study_logs
            WHERE user_id = ? AND date >= ?
            ORDER BY date ASC;
        """, (user_id, start_date))
        return [dict(row) for row in cursor.fetchall()]
