
import pandas as pd
import sqlite3
import json
from collections import defaultdict
pd.set_option('future.no_silent_downcasting', True)

def get_schedule(timetable, grade, file_path, sheet_name):
    # Excelファイルの指定シートを読み込む
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # B列に日付が入っていない行を削除
    df = df[pd.to_datetime(df.iloc[:, 1], format='%Y-%m-%d', errors='coerce').notnull()]
    df = df.fillna('').infer_objects(copy=False)

    courses = defaultdict(int)
    rooms = defaultdict(int)
    for index, row in df.iterrows():
        date = pd.to_datetime(row.iloc[1]).strftime('%Y-%m-%d')  # 日付をフォーマット
        comment = row.iloc[13]
        if comment:
            course = {'grade': grade, 'date': date,  'period': 0, 'courses': '', 'room': '', 'comment': comment}
            timetable.append(course)
        for i in range(1, 6): 
            course_name = row.iloc[i*2+1]
            room = row.iloc[i*2+2]
            if not course_name:
                continue
            course = {'grade': grade, 'date': date,  'period': i, 'courses': course_name, 'room': room, 'comment': ''}
            courses[course_name] += 1
            rooms[room] += 1
            timetable.append(course)
    return timetable, courses, rooms

file_path = 'first.xlsx'
sheet_names = {
    '2025年度(1年前期)': '1年生',
    '2025年度(2年前期)': '2年生',
    '2025年度(3年前期)': '3年生',
    '2025年度(4年前期)': '4年生',
    '2025年度(助産前期)': '4年生助産',
}

timetable = []
for sheet_name, grade_name in sheet_names.items():
    schedule, courses, rooms = get_schedule(timetable, grade_name, file_path, sheet_name)
    
    # コース情報を表示
    print(f"コース情報 ({grade_name}):")
    for course, count in courses.items():
        print(f"  {course}: {count}回")

def save_to_sqlite(timetable, db_path='schedule.db'):
    """
    時間割データをSQLiteデータベースに保存する関数
    
    Args:
        timetable (list): 時間割データのリスト
        db_path (str): SQLiteデータベースのパス
    """
    # SQLiteデータベースに接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # テーブルを作成（存在しない場合）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grade TEXT,
        date TEXT,
        period INTEGER,
        courses TEXT,
        room TEXT,
        comment TEXT
    )
    ''')

    # データを挿入する前に既存のデータを削除
    cursor.execute('DELETE FROM schedule')

    # データをSQLiteに挿入
    for course in timetable:
        cursor.execute('''
        INSERT INTO schedule (grade, date, period, courses, room, comment)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            course['grade'],
            course['date'],
            course['period'],
            course['courses'],
            course['room'],
            course['comment']
        ))

    # 変更をコミットして接続を閉じる
    conn.commit()
    conn.close()
    
    print(f'{db_path}に保存しました。')

def save_to_json(timetable, json_path='schedule.json'):
    """
    時間割データをJSON形式で保存する関数
    
    Args:
        timetable (list): 時間割データのリスト
        json_path (str): 保存するJSONファイルのパス
    """
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(timetable, f, ensure_ascii=False, indent=2)
    
    print(f'{json_path}に保存しました。')

# SQLiteとJSONに保存
save_to_sqlite(timetable)
save_to_json(timetable)
