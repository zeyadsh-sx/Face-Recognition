from datetime import date
from core.database_core_mysql import MySQLAttendanceDatabase
from core.attendance_service import AttendanceService

try:
    db = MySQLAttendanceDatabase(host='localhost', user='root', password='', database='attendance_system', port=3306)
    service = AttendanceService(db)
    ok, msg = service.start_lecture('Test Lecture', 'CS101', 'Dr Test', section='A', late_threshold=10)
    print('start_lecture:', ok, msg)
    if ok:
        lecture_id = msg
        active = db.get_active_lecture()
        print('active lecture:', active)
        # record a quick attendance for the active lecture if students exist
        students = db.get_all_students_v2()
        if students:
            student_id = students[0]['id']
            att_ok, att_msg = db.record_attendance_sighting(
                student_id=student_id,
                date_str=date.today().isoformat(),
                time_str='08:00:00',
                attendance_status='present',
                lecture_id=lecture_id,
                late_minutes=0,
            )
            print('attendance record:', att_ok, att_msg)

        ok2, msg2, summary = service.end_lecture()
        print('end_lecture:', ok2, msg2)
        print('summary:', summary)

        with db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT id, start_time, end_time, total_attendees FROM lecture_sessions WHERE id = %s', (lecture_id,))
            row = cursor.fetchone()
            print('lecture db row:', row)
            if row:
                assert row['end_time'] is not None, 'Lecture end_time was not saved'

        board = db.get_attendance_board(date.today().isoformat(), lecture_id)
        print('lecture board:', board)
        assert board.get('lecture_id') == lecture_id, 'Lecture board did not filter by lecture_id'
except Exception as e:
    print('Exception:', e)
