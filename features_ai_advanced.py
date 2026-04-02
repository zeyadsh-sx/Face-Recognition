import cv2
import numpy as np
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not available, using fallback methods")
from datetime import datetime
import os
import json
import threading
import time
from collections import deque
import pickle

class AntiSpoofing:
    """Anti-spoofing detection using various techniques"""
    
    def __init__(self):
        self.blink_detector = BlinkDetector()
        self.motion_detector = MotionDetector()
        self.texture_analyzer = TextureAnalyzer()
        
    def is_real_face(self, face_region, frame):
        """Check if the face is real using multiple techniques"""
        try:
            # Blink detection
            blink_score = self.blink_detector.detect_blink(face_region)
            
            # Motion detection
            motion_score = self.motion_detector.detect_motion(face_region)
            
            # Texture analysis
            texture_score = self.texture_analyzer.analyze_texture(face_region)
            
            # Combined score
            combined_score = (blink_score * 0.4) + (motion_score * 0.3) + (texture_score * 0.3)
            
            return combined_score > 0.6, combined_score
            
        except Exception as e:
            print(f"Anti-spoofing error: {e}")
            return True, 0.5  # Default to real if error occurs

class BlinkDetector:
    """Detect eye blinks to verify liveness"""
    
    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.blink_history = deque(maxlen=10)
        self.last_blink_time = time.time()
        
    def detect_blink(self, face_region):
        """Detect if person blinked recently"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 5)
            
            if len(eyes) >= 2:
                # Calculate eye aspect ratio (simplified)
                current_time = time.time()
                if current_time - self.last_blink_time < 2:
                    return 0.8  # Recent blink detected
                
                self.last_blink_time = current_time
                return 0.7
            
            return 0.3
            
        except Exception:
            return 0.5

class MotionDetector:
    """Detect subtle facial movements"""
    
    def __init__(self):
        self.previous_frame = None
        self.motion_threshold = 0.02
        
    def detect_motion(self, face_region):
        """Detect micro-movements in face region"""
        try:
            if self.previous_frame is None:
                self.previous_frame = face_region.copy()
                return 0.5
            
            # Calculate optical flow (simplified)
            gray_prev = cv2.cvtColor(self.previous_frame, cv2.COLOR_BGR2GRAY)
            gray_curr = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Simple difference calculation
            diff = cv2.absdiff(gray_prev, gray_curr)
            motion_score = np.mean(diff) / 255.0
            
            self.previous_frame = face_region.copy()
            
            # Normalize score
            return min(motion_score * 10, 1.0)
            
        except Exception:
            return 0.5

class TextureAnalyzer:
    """Analyze facial texture patterns"""
    
    def __init__(self):
        pass
        
    def analyze_texture(self, face_region):
        """Analyze texture to detect printed/photos"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Calculate local binary patterns (simplified)
            lbp = self.calculate_lbp(gray)
            
            # Analyze texture variance
            texture_variance = np.var(lbp)
            
            # Real faces have higher texture variance
            if texture_variance > 50:
                return 0.8
            elif texture_variance > 30:
                return 0.6
            else:
                return 0.3
                
        except Exception:
            return 0.5
    
    def calculate_lbp(self, image, radius=1, neighbors=8):
        """Calculate Local Binary Pattern (simplified version)"""
        height, width = image.shape
        lbp = np.zeros((height, width), dtype=np.uint8)
        
        for i in range(radius, height - radius):
            for j in range(radius, width - radius):
                center = image[i, j]
                binary_string = ""
                
                for n in range(neighbors):
                    angle = 2 * np.pi * n / neighbors
                    x = i + radius * np.cos(angle)
                    y = j + radius * np.sin(angle)
                    
                    # Bilinear interpolation
                    x1, y1 = int(x), int(y)
                    x2, y2 = min(x1 + 1, height - 1), min(y1 + 1, width - 1)
                    
                    dx, dy = x - x1, y - y1
                    interpolated = (1 - dx) * (1 - dy) * image[x1, y1] + \
                                  dx * (1 - dy) * image[x2, y1] + \
                                  (1 - dx) * dy * image[x1, y2] + \
                                  dx * dy * image[x2, y2]
                    
                    binary_string += "1" if interpolated >= center else "0"
                
                lbp[i, j] = int(binary_string, 2)
        
        return lbp

class EmotionDetector:
    """Detect emotions from facial expressions"""
    
    def __init__(self):
        self.emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        # In a real implementation, you would load a pre-trained model here
        # For demonstration, we'll use a simplified approach
        
    def detect_emotion(self, face_region):
        """Detect emotion from face region"""
        try:
            # Convert to grayscale for processing
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Simplified emotion detection based on facial features
            # In practice, you would use a deep learning model like:
            # - FER (Facial Expression Recognition)
            # - DeepFace
            # - Custom CNN model
            
            # For demo purposes, return random emotion with confidence
            emotion_scores = self.analyze_facial_features(gray)
            
            # Get top emotion
            top_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[top_emotion]
            
            return {
                'emotion': top_emotion,
                'confidence': confidence,
                'all_scores': emotion_scores
            }
            
        except Exception as e:
            print(f"Emotion detection error: {e}")
            return {
                'emotion': 'neutral',
                'confidence': 0.5,
                'all_scores': {label: 0.5 for label in self.emotion_labels}
            }
    
    def analyze_facial_features(self, gray_face):
        """Analyze facial features for emotion detection (simplified)"""
        # This is a placeholder for actual emotion detection
        # Real implementation would use neural networks
        
        # Generate dummy scores for demonstration
        scores = {
            'happy': np.random.uniform(0.1, 0.9),
            'sad': np.random.uniform(0.1, 0.7),
            'angry': np.random.uniform(0.1, 0.6),
            'surprise': np.random.uniform(0.1, 0.8),
            'fear': np.random.uniform(0.1, 0.5),
            'disgust': np.random.uniform(0.1, 0.4),
            'neutral': np.random.uniform(0.2, 0.8)
        }
        
        # Normalize scores
        total = sum(scores.values())
        for key in scores:
            scores[key] = scores[key] / total
            
        return scores

class UnknownFaceAlert:
    """Handle unknown face detection and alerts"""
    
    def __init__(self, alert_callback=None):
        self.unknown_faces = []
        self.alert_callback = alert_callback
        self.unknown_face_dir = "unknown_faces"
        os.makedirs(self.unknown_face_dir, exist_ok=True)
        
    def handle_unknown_face(self, face_region, frame, timestamp):
        """Handle detection of unknown face"""
        try:
            # Save unknown face image
            filename = f"unknown_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(self.unknown_face_dir, filename)
            cv2.imwrite(filepath, face_region)
            
            # Record unknown face
            unknown_face_info = {
                'timestamp': timestamp.isoformat(),
                'image_path': filepath,
                'face_encoding': None  # Would store encoding if needed
            }
            
            self.unknown_faces.append(unknown_face_info)
            
            # Trigger alert
            if self.alert_callback:
                self.alert_callback(unknown_face_info)
            
            return unknown_face_info
            
        except Exception as e:
            print(f"Unknown face alert error: {e}")
            return None
    
    def get_unknown_faces(self, limit=10):
        """Get recent unknown faces"""
        return self.unknown_faces[-limit:]
    
    def save_unknown_face(self, name, face_encoding, unknown_face_info):
        """Save unknown face as known student"""
        try:
            # Move image to known faces
            from database import AttendanceDatabase
            db = AttendanceDatabase()
            
            student_id = db.add_student(name, face_encoding, unknown_face_info['image_path'])
            
            # Remove from unknown faces list
            if unknown_face_info in self.unknown_faces:
                self.unknown_faces.remove(unknown_face_info)
            
            return student_id
            
        except Exception as e:
            print(f"Error saving unknown face: {e}")
            return None

class LectureSystem:
    """Enhanced lecture system integration"""
    
    def __init__(self):
        self.lecture_sessions = {}
        self.current_lecture = None
        self.lecture_data_file = "lecture_sessions.json"
        
    def start_lecture(self, lecture_name, course_code, instructor):
        """Start a new lecture session"""
        try:
            lecture_id = f"{course_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.current_lecture = {
                'id': lecture_id,
                'name': lecture_name,
                'course_code': course_code,
                'instructor': instructor,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'attendees': [],
                'emotions_summary': {},
                'engagement_score': 0.0
            }
            
            self.lecture_sessions[lecture_id] = self.current_lecture
            self.save_lecture_data()
            
            return lecture_id
            
        except Exception as e:
            print(f"Error starting lecture: {e}")
            return None
    
    def end_lecture(self):
        """End current lecture session"""
        if self.current_lecture:
            self.current_lecture['end_time'] = datetime.now().isoformat()
            self.save_lecture_data()
            
            lecture_id = self.current_lecture['id']
            self.current_lecture = None
            
            return lecture_id
        
        return None
    
    def record_attendance(self, student_name, emotion_data=None):
        """Record student attendance in current lecture"""
        if not self.current_lecture:
            return False
        
        try:
            attendance_record = {
                'student_name': student_name,
                'timestamp': datetime.now().isoformat(),
                'emotion': emotion_data.get('emotion', 'neutral') if emotion_data else 'neutral',
                'confidence': emotion_data.get('confidence', 0.0) if emotion_data else 0.0
            }
            
            # Check if student already recorded
            student_names = [att['student_name'] for att in self.current_lecture['attendees']]
            if student_name not in student_names:
                self.current_lecture['attendees'].append(attendance_record)
                
                # Update emotions summary
                emotion = attendance_record['emotion']
                if emotion in self.current_lecture['emotions_summary']:
                    self.current_lecture['emotions_summary'][emotion] += 1
                else:
                    self.current_lecture['emotions_summary'][emotion] = 1
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error recording lecture attendance: {e}")
            return False
    
    def calculate_engagement_score(self):
        """Calculate lecture engagement score based on emotions"""
        if not self.current_lecture:
            return 0.0
        
        emotions = self.current_lecture['emotions_summary']
        total_students = len(self.current_lecture['attendees'])
        
        if total_students == 0:
            return 0.0
        
        # Engagement weights
        engagement_weights = {
            'happy': 0.9,
            'surprise': 0.8,
            'neutral': 0.6,
            'sad': 0.3,
            'angry': 0.2,
            'fear': 0.2,
            'disgust': 0.1
        }
        
        total_score = 0.0
        for emotion, count in emotions.items():
            weight = engagement_weights.get(emotion, 0.5)
            total_score += (count / total_students) * weight
        
        self.current_lecture['engagement_score'] = total_score
        return total_score
    
    def get_lecture_statistics(self, lecture_id=None):
        """Get statistics for a lecture"""
        if lecture_id:
            lecture = self.lecture_sessions.get(lecture_id)
        else:
            lecture = self.current_lecture
        
        if not lecture:
            return None
        
        return {
            'id': lecture['id'],
            'name': lecture['name'],
            'course_code': lecture['course_code'],
            'instructor': lecture['instructor'],
            'start_time': lecture['start_time'],
            'end_time': lecture['end_time'],
            'total_attendees': len(lecture['attendees']),
            'emotions_summary': lecture['emotions_summary'],
            'engagement_score': lecture.get('engagement_score', 0.0)
        }
    
    def save_lecture_data(self):
        """Save lecture data to file"""
        try:
            with open(self.lecture_data_file, 'w') as f:
                json.dump(self.lecture_sessions, f, indent=2)
        except Exception as e:
            print(f"Error saving lecture data: {e}")
    
    def load_lecture_data(self):
        """Load lecture data from file"""
        try:
            if os.path.exists(self.lecture_data_file):
                with open(self.lecture_data_file, 'r') as f:
                    self.lecture_sessions = json.load(f)
        except Exception as e:
            print(f"Error loading lecture data: {e}")
            self.lecture_sessions = {}

class AdvancedAttendanceReporter:
    """Enhanced attendance reporting with advanced features"""
    
    def __init__(self, db):
        self.db = db
        
    def generate_comprehensive_report(self, start_date, end_date):
        """Generate comprehensive attendance report"""
        try:
            # Get basic attendance data
            attendance_data = self.db.get_attendance_by_date_range(start_date, end_date)
            students = self.db.get_all_students()
            
            # Load lecture data if available
            lecture_data = self.load_lecture_data()
            
            # Generate enhanced report
            report = {
                'period': f"{start_date} to {end_date}",
                'summary': self.generate_summary_stats(attendance_data, students),
                'student_details': self.generate_student_details(attendance_data, students),
                'daily_breakdown': self.generate_daily_breakdown(attendance_data),
                'lecture_analysis': self.analyze_lecture_data(lecture_data),
                'trends': self.analyze_trends(attendance_data),
                'recommendations': self.generate_recommendations(attendance_data, students)
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating comprehensive report: {e}")
            return None
    
    def generate_summary_stats(self, attendance_data, students):
        """Generate summary statistics"""
        total_students = len(students)
        student_attendance = {}
        
        for student in students:
            student_attendance[student['name']] = {
                'present_days': 0,
                'total_days': 0,
                'late_arrivals': 0,
                'early_departures': 0
            }
        
        # Process attendance data
        for record in attendance_data:
            name = record['name']
            if name in student_attendance:
                student_attendance[name]['present_days'] += 1
                
                # Analyze arrival time (simplified)
                time_parts = record['time'].split(':')
                hour = int(time_parts[0])
                if hour > 9:  # Assuming 9 AM as start time
                    student_attendance[name]['late_arrivals'] += 1
        
        # Calculate totals
        total_present = sum(1 for s in student_attendance.values() if s['present_days'] > 0)
        avg_attendance = (total_present / total_students * 100) if total_students > 0 else 0
        
        return {
            'total_students': total_students,
            'total_present': total_present,
            'total_absent': total_students - total_present,
            'average_attendance_rate': avg_attendance,
            'total_late_arrivals': sum(s['late_arrivals'] for s in student_attendance.values())
        }
    
    def generate_student_details(self, attendance_data, students):
        """Generate detailed student attendance information"""
        student_records = {}
        
        # Initialize student records
        for student in students:
            student_records[student['name']] = {
                'total_days': 0,
                'present_days': 0,
                'attendance_rate': 0.0,
                'first_attendance': None,
                'last_attendance': None,
                'attendance_pattern': []
            }
        
        # Process attendance records
        for record in attendance_data:
            name = record['name']
            if name in student_records:
                student_records[name]['present_days'] += 1
                student_records[name]['attendance_pattern'].append({
                    'date': record['date'],
                    'time': record['time']
                })
                
                # Update first and last attendance
                if not student_records[name]['first_attendance']:
                    student_records[name]['first_attendance'] = record['date']
                student_records[name]['last_attendance'] = record['date']
        
        # Calculate attendance rates
        total_days = len(set(record['date'] for record in attendance_data))
        for name, record in student_records.items():
            record['total_days'] = total_days
            record['attendance_rate'] = (record['present_days'] / total_days * 100) if total_days > 0 else 0
        
        return student_records
    
    def generate_daily_breakdown(self, attendance_data):
        """Generate daily attendance breakdown"""
        daily_stats = {}
        
        for record in attendance_data:
            date = record['date']
            if date not in daily_stats:
                daily_stats[date] = {
                    'present': [],
                    'total_present': 0,
                    'peak_time': None,
                    'arrival_times': []
                }
            
            daily_stats[date]['present'].append(record['name'])
            daily_stats[date]['total_present'] += 1
            daily_stats[date]['arrival_times'].append(record['time'])
        
        # Calculate peak arrival time for each day
        for date, stats in daily_stats.items():
            if stats['arrival_times']:
                # Find most common arrival time (simplified)
                time_counts = {}
                for time in stats['arrival_times']:
                    hour = int(time.split(':')[0])
                    time_counts[hour] = time_counts.get(hour, 0) + 1
                
                peak_hour = max(time_counts, key=time_counts.get)
                stats['peak_time'] = f"{peak_hour}:00"
        
        return daily_stats
    
    def analyze_lecture_data(self, lecture_data):
        """Analyze lecture session data"""
        if not lecture_data:
            return {}
        
        analysis = {
            'total_lectures': len(lecture_data),
            'average_attendance': 0,
            'average_engagement': 0,
            'emotion_trends': {},
            'top_performing_lectures': []
        }
        
        total_attendance = 0
        total_engagement = 0
        all_emotions = {}
        
        for lecture_id, lecture in lecture_data.items():
            attendees = len(lecture.get('attendees', []))
            engagement = lecture.get('engagement_score', 0)
            emotions = lecture.get('emotions_summary', {})
            
            total_attendance += attendees
            total_engagement += engagement
            
            # Aggregate emotions
            for emotion, count in emotions.items():
                all_emotions[emotion] = all_emotions.get(emotion, 0) + count
        
        if len(lecture_data) > 0:
            analysis['average_attendance'] = total_attendance / len(lecture_data)
            analysis['average_engagement'] = total_engagement / len(lecture_data)
            analysis['emotion_trends'] = all_emotions
        
        return analysis
    
    def analyze_trends(self, attendance_data):
        """Analyze attendance trends over time"""
        # Group by week
        weekly_data = {}
        
        for record in attendance_data:
            date_obj = datetime.strptime(record['date'], '%Y-%m-%d')
            week_number = date_obj.isocalendar()[1]
            year = date_obj.year
            week_key = f"{year}-W{week_number}"
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {'present': 0, 'unique_students': set()}
            
            weekly_data[week_key]['present'] += 1
            weekly_data[week_key]['unique_students'].add(record['name'])
        
        # Convert to list and sort
        trend_data = []
        for week_key, data in sorted(weekly_data.items()):
            trend_data.append({
                'week': week_key,
                'total_attendance': data['present'],
                'unique_students': len(data['unique_students'])
            })
        
        return trend_data
    
    def generate_recommendations(self, attendance_data, students):
        """Generate recommendations based on attendance data"""
        recommendations = []
        
        # Analyze attendance patterns
        student_attendance = {}
        for student in students:
            student_attendance[student['name']] = 0
        
        for record in attendance_data:
            if record['name'] in student_attendance:
                student_attendance[record['name']] += 1
        
        # Find students with low attendance
        low_attendance = []
        total_days = len(set(record['date'] for record in attendance_data))
        
        for name, count in student_attendance.items():
            attendance_rate = (count / total_days * 100) if total_days > 0 else 0
            if attendance_rate < 70:
                low_attendance.append({'name': name, 'rate': attendance_rate})
        
        if low_attendance:
            recommendations.append({
                'type': 'attendance_improvement',
                'priority': 'high',
                'message': f"{len(low_attendance)} طلاب لديهم معدل حضور أقل من 70%",
                'students': low_attendance[:5]  # Top 5
            })
        
        # Peak time analysis
        arrival_hours = []
        for record in attendance_data:
            hour = int(record['time'].split(':')[0])
            arrival_hours.append(hour)
        
        if arrival_hours:
            peak_hour = max(set(arrival_hours), key=arrival_hours.count)
            recommendations.append({
                'type': 'schedule_optimization',
                'priority': 'medium',
                'message': f"معظم الطلاب يحضرون الساعة {peak_hour}:00",
                'suggested_time': f"{peak_hour}:00"
            })
        
        return recommendations
    
    def load_lecture_data(self):
        """Load lecture data from file"""
        try:
            if os.path.exists("lecture_sessions.json"):
                with open("lecture_sessions.json", 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading lecture data: {e}")
        
        return {}
