# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "openpyxl",
#     "pandas",
# ]
# ///
import pandas as pd
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

    courses_json = json.dumps(courses, ensure_ascii=False, indent=4)
    print(courses_json)

    path = 'schedule.json'
    json.dump(schedule, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
    print(f'{path}に保存しました。')
