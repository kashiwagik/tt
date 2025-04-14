
import pandas as pd
import json
from collections import defaultdict
import sqlite3

# 以下のエラー抑制のための設定
# FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version. 
pd.set_option('future.no_silent_downcasting', True)


def get_schedule(file_path, sheet_name, grade):
    timetable = []

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


def add_schedule_to_josan(timetable):
    """
    助産前期の時間割を4年生の時間割に追加する関数
    """
    forth_grade = {}
    josan_course = {}

    # それぞれの時間割を辞書に変換
    for course in timetable:
        if course['grade'] == '4年生':
            forth_grade[course["date"] + str(course["period"])] = course
        elif course['grade'] == '4年生助産':
            josan_course[course["date"] + str(course["period"])] = course

    # 4年生の時間割を助産前期の時間割に追加
    for key, course in forth_grade.items():
        # すでに助産前期の時間割が存在する場合はスキップ
        if key in josan_course:
            continue
        course['grade'] = '4年生助産'
        timetable.append(course)

    return timetable

    
def main(file_path, sheet_names, json_path):
    for sheet_name, grade_name in sheet_names.items():
        print(f"コース情報 ({grade_name}):")
        timetable, courses, rooms = get_schedule(file_path, sheet_name, grade_name)
        
        # コース情報を表示
        # print(f"コース情報 ({grade_name}):")
        # for course, count in courses.items():
        #     print(f"  {course}: {count}回")
    
    # 4年生の時間割を4年生助産に追加
    timetable = add_schedule_to_josan(timetable)

    # SQLite
    # save_to_sqlite(timetable)
    # JSONに保存
    save_to_json(timetable, json_path)


if __name__ == "__main__":
    excel_path = '【2025・04～09月 前期】全学年時間割.xlsx'
    sheet_names = {
        '2025年度(1年前期)': '1年生',
        '2025年度(2年前期)': '2年生',
        '2025年度(3年前期)': '3年生',
        '2025年度(4年前期)': '4年生',
        '2025年度(助産前期)': '4年生助産',
        '2025年度(M1前期)': 'M1',
        '2025年度(M2前期)': 'M2',
        '2025年度(D1前期)': 'D1',
        '2025年度(D23前期)': 'D23',
    }
    json_path = 'docs/schedule.json'

    main(excel_path, sheet_names, json_path)
    
