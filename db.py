import sqlite3
import datetime
from typing import Dict, List, Optional, Tuple, Any

# Путь к базе данных
DB_PATH = "bankruptcy_bot.db"

def init_db():
    """Инициализирует базу данных и создает необходимые таблицы."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица для заявок на консультацию
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            debt_amount REAL,
            income REAL,
            case_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new',
            ai_analysis TEXT
        )
    """)
    
    # Таблица для записей на консультации
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            datetime TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'scheduled',
            notes TEXT
        )
    """)
    
    # Таблица для расписания юриста
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lawyer_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Таблица для хранения данных пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            debt_amount REAL,
            income REAL,
            case_description TEXT,
            ai_requests_count INTEGER DEFAULT 0,
            last_ai_request_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица для анализов документов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            document_type TEXT,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def save_request(user_id: int, username: str, full_name: str, phone: str, 
                 debt_amount: float, income: float, case_description: str, 
                 ai_analysis: str = None) -> int:
    """Сохраняет заявку на консультацию."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO requests (user_id, username, full_name, phone, debt_amount, 
                            income, case_description, ai_analysis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, full_name, phone, debt_amount, income, 
          case_description, ai_analysis))
    
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return request_id

def save_appointment(user_id: int, username: str, full_name: str, phone: str, 
                    appointment_datetime: str) -> int:
    """Сохраняет запись на консультацию."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO appointments (user_id, username, full_name, phone, datetime)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, full_name, phone, appointment_datetime))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return appointment_id

def save_client_data(user_id: int, data: Dict[str, Any]):
    """Сохраняет или обновляет данные клиента."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем, существует ли запись
    cursor.execute("SELECT user_id FROM user_data WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if exists:
        # Обновляем существующую запись
        update_parts = []
        values = []
        for key, value in data.items():
            if key != 'user_id':
                update_parts.append(f"{key} = ?")
                values.append(value)
        
        values.append(user_id)
        query = f"""
            UPDATE user_data 
            SET {', '.join(update_parts)}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """
        cursor.execute(query, values)
    else:
        # Создаем новую запись
        columns = ['user_id'] + list(data.keys())
        values = [user_id] + list(data.values())
        placeholders = ', '.join(['?' for _ in values])
        columns_str = ', '.join(columns)
        
        query = f"""
            INSERT INTO user_data ({columns_str})
            VALUES ({placeholders})
        """
        cursor.execute(query, values)
    
    conn.commit()
    conn.close()

def get_client_data(user_id: int) -> Optional[Dict[str, Any]]:
    """Получает данные клиента."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_data WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        columns = [description[0] for description in cursor.description]
        data = dict(zip(columns, row))
    else:
        data = None
    
    conn.close()
    return data

def get_all_requests() -> List[Tuple]:
    """Получает все заявки на консультацию."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM requests 
        ORDER BY created_at DESC
    """)
    
    requests = cursor.fetchall()
    conn.close()
    
    return requests

def get_request_details(request_id: int) -> Optional[Tuple]:
    """Получает детали конкретной заявки."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    request = cursor.fetchone()
    
    conn.close()
    return request

def update_request_status(request_id: int, status: str):
    """Обновляет статус заявки."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE requests 
        SET status = ? 
        WHERE id = ?
    """, (status, request_id))
    
    conn.commit()
    conn.close()

def get_appointments_for_date(date: datetime.date) -> List[Tuple]:
    """Получает все записи на указанную дату."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    date_str = date.isoformat()
    cursor.execute("""
        SELECT * FROM appointments 
        WHERE date(appointments.datetime) = ? 
        ORDER BY appointments.datetime
    """, (date_str,))
    
    appointments = cursor.fetchall()
    conn.close()
    
    return appointments

def get_booked_times_for_date(date: datetime.date) -> List[str]:
    """Получает список забронированных времен на указанную дату."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    date_str = date.isoformat()
    cursor.execute("""
        SELECT strftime('%H:%M', appointments.datetime) FROM appointments 
        WHERE date(appointments.datetime) = ? 
        AND status != 'cancelled'
    """, (date_str,))
    
    booked_times = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return booked_times

def check_appointment_time_available(date: datetime.date, time: str) -> bool:
    """Проверяет доступность времени для записи."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    datetime_str = f"{date.isoformat()}T{time}:00"
    cursor.execute("""
        SELECT COUNT(*) FROM appointments 
        WHERE appointments.datetime = ? 
        AND status != 'cancelled'
    """, (datetime_str,))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count == 0

def save_lawyer_schedule(schedule: List[Tuple[str, str, str]]):
    """Сохраняет расписание юриста."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Удаляем старое расписание
    cursor.execute("DELETE FROM lawyer_schedule")
    
    # Сохраняем новое расписание
    for day, start_time, end_time in schedule:
        cursor.execute("""
            INSERT INTO lawyer_schedule (day_of_week, start_time, end_time)
            VALUES (?, ?, ?)
        """, (day, start_time, end_time))
    
    conn.commit()
    conn.close()

def get_lawyer_schedule() -> List[Tuple[str, str, str]]:
    """Получает расписание юриста."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT day_of_week, start_time, end_time 
        FROM lawyer_schedule 
        WHERE is_active = 1
    """)
    
    schedule = cursor.fetchall()
    conn.close()
    
    return schedule

def update_ai_request_count(user_id: int):
    """Обновляет счетчик запросов к ИИ."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.date.today().isoformat()
    
    # Проверяем существует ли запись
    cursor.execute("SELECT ai_requests_count, last_ai_request_date FROM user_data WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        last_date = result[1]
        if last_date == today:
            # Увеличиваем счетчик
            cursor.execute("""
                UPDATE user_data 
                SET ai_requests_count = ai_requests_count + 1
                WHERE user_id = ?
            """, (user_id,))
        else:
            # Новый день - сбрасываем счетчик
            cursor.execute("""
                UPDATE user_data 
                SET ai_requests_count = 1,
                    last_ai_request_date = ?
                WHERE user_id = ?
            """, (today, user_id))
    else:
        # Создаем новую запись
        cursor.execute("""
            INSERT INTO user_data (user_id, ai_requests_count, last_ai_request_date)
            VALUES (?, 1, ?)
        """, (user_id, today))
    
    conn.commit()
    conn.close()

def get_ai_request_count(user_id: int) -> int:
    """Получает количество запросов к ИИ за сегодня."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.date.today().isoformat()
    
    cursor.execute("""
        SELECT ai_requests_count 
        FROM user_data 
        WHERE user_id = ? AND last_ai_request_date = ?
    """, (user_id, today))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    return 0

def get_todays_appointments() -> List[Tuple]:
    """Получает записи на сегодня."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.date.today().isoformat()
    cursor.execute("""
        SELECT username, full_name, phone, appointments.datetime 
        FROM appointments 
        WHERE date(appointments.datetime) = ?
        ORDER BY appointments.datetime
    """, (today,))
    
    appointments = cursor.fetchall()
    conn.close()
    
    return appointments

def get_new_requests_for_day() -> List[Tuple]:
    """Получает новые заявки за сегодня."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.date.today().isoformat()
    cursor.execute("""
        SELECT username, full_name, phone, case_description 
        FROM requests 
        WHERE date(created_at) = ? AND status = 'new'
        ORDER BY created_at DESC
    """, (today,))
    
    requests = cursor.fetchall()
    conn.close()
    
    return requests

def get_statistics() -> dict:
    """Получает статистику для админ-панели."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    try:
        # Общее количество заявок
        cursor.execute("SELECT COUNT(*) FROM requests")
        stats['total_requests'] = cursor.fetchone()[0]
        
        # Заявки по статусам
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'new'")
        stats['new_requests'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'in_progress'")
        stats['in_progress'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'completed'")
        stats['completed'] = cursor.fetchone()[0]
        
        # Консультации
        cursor.execute("""
            SELECT COUNT(*) FROM appointments 
            WHERE datetime(appointments.datetime) >= datetime('now', 'localtime')
        """)
        stats['scheduled'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM appointments 
            WHERE datetime(appointments.datetime) < datetime('now', 'localtime')
        """)
        stats['completed_appointments'] = cursor.fetchone()[0]
        
        # Клиенты
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM requests")
        stats['total_clients'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM requests 
            WHERE created_at >= date('now', '-30 days')
        """)
        stats['active_clients'] = cursor.fetchone()[0]
        
        # Финансы
        cursor.execute("""
            SELECT SUM(debt_amount), AVG(debt_amount) 
            FROM requests 
            WHERE debt_amount > 0
        """)
        result = cursor.fetchone()
        stats['total_debt'] = result[0] or 0
        stats['avg_debt'] = result[1] or 0
        
        # Потенциальный доход
        cursor.execute("""
            SELECT SUM(debt_amount) 
            FROM requests 
            WHERE status = 'completed' AND debt_amount > 0
        """)
        completed_debt = cursor.fetchone()[0] or 0
        stats['potential_income'] = completed_debt * 0.1
        
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        stats = {
            'total_requests': 0,
            'new_requests': 0,
            'in_progress': 0,
            'completed': 0,
            'scheduled': 0,
            'completed_appointments': 0,
            'total_clients': 0,
            'active_clients': 0,
            'total_debt': 0,
            'avg_debt': 0,
            'potential_income': 0
        }
    
    conn.close()
    return stats

def export_client_data(user_id: int) -> dict:
    """Экспортирует все данные клиента."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    data = {}
    
    # Данные из requests
    cursor.execute("SELECT * FROM requests WHERE user_id = ?", (user_id,))
    data['requests'] = cursor.fetchall()
    
    # Данные из appointments
    cursor.execute("SELECT * FROM appointments WHERE user_id = ?", (user_id,))
    data['appointments'] = cursor.fetchall()
    
    # Данные из user_data
    cursor.execute("SELECT * FROM user_data WHERE user_id = ?", (user_id,))
    data['user_data'] = cursor.fetchone()
    
    conn.close()
    return data

def save_document_analysis(user_id: int, document_type: str, analysis: str):
    """Сохраняет результат анализа документа."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO document_analyses (user_id, document_type, analysis)
        VALUES (?, ?, ?)
    """, (user_id, document_type, analysis))
    
    conn.commit()
    conn.close()
