from datetime import datetime, timezone, timedelta
import os
import pandas as pd
import json
from collections import defaultdict

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
        elif course['grade'] == '4年助産':
            josan_course[course["date"] + str(course["period"])] = course

    # 4年生の時間割を助産前期の時間割に追加
    for key, course in forth_grade.items():
        # すでに助産前期の時間割が存在する場合はスキップ
        if key in josan_course:
            continue
        # 卒業研究は除外
        #if course['courses'].startswith('卒業研究'):
        #    continue
        new_course = course.copy()
        new_course['grade'] = '4年助産'
        timetable.append(new_course)

    return timetable

def make_info_json(file_path, info_json_path):
    # ファイルの更新時刻を取得
    file_stat = os.stat(file_path)
    # 日本時間（UTC+9）のタイムゾーンを定義
    jst = timezone(timedelta(hours=9))
    # UTCタイムスタンプを日本時間に変換
    modified_time = datetime.fromtimestamp(file_stat.st_mtime, tz=jst).strftime('%Y-%m-%d %H:%M:%S')

    # 更新時刻をinfo.jsonに書き込む
    info_data = {"file_path": file_path, "last_modified": modified_time}
    with open(info_json_path, 'w', encoding='utf-8') as f:
        json.dump(info_data, f, ensure_ascii=False, indent=2)

    print(f'{info_json_path}に更新時刻を保存しました。')
    
    
def main(file_path, sheet_names, json_path, info_json_path):
    # info.jsonを作成
    make_info_json(file_path, info_json_path)

    all_timetable = []
    for sheet_name, grade_name in sheet_names.items():
        print(f"コース情報 ({grade_name}):")
        timetable, courses, rooms = get_schedule(file_path, sheet_name, grade_name)
        all_timetable.extend(timetable)

    # 4年生の時間割を4年生助産に追加
    all_timetable = add_schedule_to_josan(all_timetable)

    # JSONに保存
    save_to_json(all_timetable, json_path)


if __name__ == "__main__":
    excel_path = 'schedule.xlsx'
    sheet_names = {
        '2025年度(1年前期)': '1年生',
        '2025年度(2年前期)': '2年生',
        '2025年度(3年前期)': '3年生',
        '2025年度(4年前期)': '4年生',
        '2025年度(助産前期)': '4年助産',
        '2025年度(M1前期)': 'M1',
        '2025年度(M2前期)': 'M2',
        '2025年度(D1前期)': 'D1',
        '2025年度(D23前期)': 'D23',
    }
    json_path = 'docs/schedule.json'
    # info.jsonのパスを指定
    info_json_path = 'docs/info.json'

    main(excel_path, sheet_names, json_path, info_json_path)
