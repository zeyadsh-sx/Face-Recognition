"""Flask API routes for attendance v2."""
from datetime import date
from pathlib import Path

from flask import jsonify, request, send_file

from core.attendance_service import AttendanceService


def register_attendance_routes(app, db):
    service = AttendanceService(db)

    @app.route("/api/attendance/board", methods=["GET"])
    def api_attendance_board():
        d = request.args.get("date") or date.today().isoformat()
        return jsonify(db.get_attendance_board(d))

    @app.route("/api/attendance/report", methods=["GET"])
    def api_absence_report():
        d = request.args.get("date") or date.today().isoformat()
        return jsonify(service.export_absence_report(d))

    @app.route("/api/attendance/report/pdf", methods=["GET"])
    def api_attendance_report_pdf():
        d = request.args.get("date") or date.today().isoformat()
        lecture = request.args.get("lecture_name")
        ok, result = service.export_report_pdf(d, lecture_name=lecture)
        if not ok:
            return jsonify({"success": False, "message": result}), 500
        return send_file(
            Path(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=Path(result).name,
        )

    @app.route("/api/lecture/active", methods=["GET"])
    def api_active_lecture():
        lec = db.get_active_lecture()
        return jsonify({"active": lec is not None, "lecture": lec})

    @app.route("/api/lecture/start", methods=["POST"])
    def api_start_lecture():
        data = request.get_json(silent=True) or {}
        ok, msg = service.start_lecture(
            data.get("name", "محاضرة"),
            data.get("course_code", ""),
            data.get("instructor", ""),
            data.get("section"),
            data.get("late_threshold_minutes"),
        )
        return jsonify({"success": ok, "lecture_id": msg if ok else None, "message": msg})

    @app.route("/api/lecture/end", methods=["POST"])
    def api_end_lecture():
        ok, msg, summary = service.end_lecture()
        return jsonify({"success": ok, "message": msg, "summary": summary})

    @app.route("/api/attendance/manual", methods=["POST"])
    def api_manual_attendance():
        data = request.get_json(silent=True) or {}
        student_id = data.get("student_id")
        status = data.get("status", "present")
        d = data.get("date") or date.today().isoformat()
        if not student_id:
            return jsonify({"success": False, "message": "student_id required"}), 400
        ok, msg = db.set_manual_attendance_status(
            int(student_id), d, status, reason=data.get("reason")
        )
        return jsonify({"success": ok, "message": msg})

    @app.route("/api/schedule", methods=["GET", "POST"])
    def api_schedule():
        if request.method == "GET":
            day = request.args.get("day")
            day_i = int(day) if day is not None else None
            return jsonify(db.get_schedule(day_i))
        data = request.get_json(silent=True) or {}
        ok = db.add_schedule_entry(
            data.get("course_name", ""),
            data.get("course_code", ""),
            data.get("section", ""),
            int(data.get("day_of_week", 0)),
            data.get("start_time", "08:00:00"),
            data.get("end_time", "10:00:00"),
            data.get("instructor", ""),
            data.get("room", ""),
        )
        return jsonify({"success": ok})

    @app.route("/api/students", methods=["GET"])
    def api_students_list():
        section = request.args.get("section")
        return jsonify(db.get_students_filtered(section))

    @app.route("/api/email/config", methods=["GET"])
    def api_email_config():
        from core.email_service import load_email_config
        cfg = load_email_config()
        safe = {k: v for k, v in cfg.items() if k != "password"}
        safe["password_set"] = bool(cfg.get("password"))
        return jsonify(safe)

    @app.route("/api/email/test", methods=["POST"])
    def api_email_test():
        ok, msg = service.send_test_email()
        return jsonify({"success": ok, "message": msg})

    @app.route("/api/email/report", methods=["POST"])
    def api_email_report():
        data = request.get_json(silent=True) or {}
        d = data.get("date") or date.today().isoformat()
        include = bool(data.get("include_students", False))
        ok, msg = service.send_email_report(d, include_students=include)
        return jsonify({"success": ok, "message": msg})
