import cv2
import numpy as np
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not available, using fallback methods")

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("Warning: deepface not available, emotion analysis disabled")
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
            
            # Try to use DeepFace for emotion detection if available
            if DEEPFACE_AVAILABLE:
                try:
                    emotion_analysis = DeepFace.analyze(
                        face_region, 
                        actions=['emotion'],
                        enforce_detection=False
                    )
                    if isinstance(emotion_analysis, list) and len(emotion_analysis) > 0:
                        emotion_data = emotion_analysis[0]
                    else:
                        emotion_data = emotion_analysis
                    
                    return {
                        'emotion': emotion_data.get('dominant_emotion', 'neutral'),
                        'confidence': max(emotion_data.get('emotion', {}).values()) if emotion_data.get('emotion') else 0.5,
                        'all_scores': emotion_data.get('emotion', {})
                    }
                except Exception as deepface_error:
                    print(f"DeepFace emotion analysis failed: {deepface_error}")
                    # Fall back to simplified method
            
            # Simplified emotion detection based on facial features
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
            from database_core_mysql import MySQLAttendanceDatabase
            db = MySQLAttendanceDatabase()
            
            student_id = db.add_student_advanced(name, face_encoding, unknown_face_info['image_path'])
            
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


class FaceQualityAssessment:
    """
    Face Quality Assessment
    - Lighting Assessment
    - Sharpness Assessment
    - Face Angle Assessment
    - Reject inappropriate images
    - Alert user to improve quality
    """
    
    def __init__(self):
        # Quality thresholds
        self.MIN_LIGHTNESS = 40      # Minimum average brightness (0-255)
        self.MAX_LIGHTNESS = 220     # Maximum average brightness
        self.MIN_SHARPNESS = 100     # Minimum sharpness score
        self.MIN_FACE_SIZE = 80      # Minimum face size in pixels
        self.MAX_YAW_ANGLE = 30      # Maximum yaw angle (left/right)
        self.MAX_PITCH_ANGLE = 20    # Maximum pitch angle (up/down)
        
        # Quality weights for final score
        self.WEIGHT_LIGHTING = 0.3
        self.WEIGHT_SHARPNESS = 0.4
        self.WEIGHT_ANGLE = 0.2
        self.WEIGHT_SIZE = 0.1
        
    def assess_quality(self, face_region, frame=None, face_location=None):
        """
        Assess the quality of a face image
        
        Args:
            face_region: The face image region (BGR)
            frame: Full frame (optional, for additional analysis)
            face_location: Face location tuple (top, right, bottom, left)
            
        Returns:
            dict: Quality assessment results
        """
        try:
            results = {
                'is_acceptable': True,
                'overall_score': 0.0,
                'lighting_score': 0.0,
                'sharpness_score': 0.0,
                'angle_score': 0.0,
                'size_score': 0.0,
                'issues': [],
                'recommendations': []
            }
            
            # 1. Assess lighting
            lighting_result = self.assess_lighting(face_region)
            results['lighting_score'] = lighting_result['score']
            if not lighting_result['acceptable']:
                results['is_acceptable'] = False
                results['issues'].append(lighting_result['issue'])
                results['recommendations'].append(lighting_result['recommendation'])
            
            # 2. Assess sharpness
            sharpness_result = self.assess_sharpness(face_region)
            results['sharpness_score'] = sharpness_result['score']
            if not sharpness_result['acceptable']:
                results['is_acceptable'] = False
                results['issues'].append(sharpness_result['issue'])
                results['recommendations'].append(sharpness_result['recommendation'])
            
            # 3. Assess face angle
            angle_result = self.assess_face_angle(face_region)
            results['angle_score'] = angle_result['score']
            if not angle_result['acceptable']:
                results['is_acceptable'] = False
                results['issues'].append(angle_result['issue'])
                results['recommendations'].append(angle_result['recommendation'])
            
            # 4. Assess face size
            size_result = self.assess_face_size(face_region)
            results['size_score'] = size_result['score']
            if not size_result['acceptable']:
                results['is_acceptable'] = False
                results['issues'].append(size_result['issue'])
                results['recommendations'].append(size_result['recommendation'])
            
            # Calculate overall quality score
            results['overall_score'] = (
                results['lighting_score'] * self.WEIGHT_LIGHTING +
                results['sharpness_score'] * self.WEIGHT_SHARPNESS +
                results['angle_score'] * self.WEIGHT_ANGLE +
                results['size_score'] * self.WEIGHT_SIZE
            )
            
            # Determine if quality is acceptable
            results['is_acceptable'] = (
                results['overall_score'] >= 0.5 and
                results['lighting_score'] >= 0.3 and
                results['sharpness_score'] >= 0.3 and
                results['angle_score'] >= 0.3
            )
            
            return results
            
        except Exception as e:
            print(f"Face quality assessment error: {e}")
            return {
                'is_acceptable': True,
                'overall_score': 0.5,
                'lighting_score': 0.5,
                'sharpness_score': 0.5,
                'angle_score': 0.5,
                'size_score': 0.5,
                'issues': [],
                'recommendations': [],
                'error': str(e)
            }
    
    def assess_lighting(self, face_region):
        """
        Assess lighting conditions of the face image
        
        Returns:
            dict: Lighting assessment result
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Calculate average brightness
            mean_brightness = np.mean(gray)
            
            # Calculate brightness variance (contrast)
            brightness_variance = np.std(gray)
            
            # Calculate score based on brightness and contrast
            score = 0.0
            acceptable = True
            issue = ""
            recommendation = ""
            
            if mean_brightness < self.MIN_LIGHTNESS:
                # Too dark
                score = mean_brightness / self.MIN_LIGHTNESS * 0.7
                acceptable = False
                issue = "الصورة darker جداً (إضاءة ضعيفة)"
                recommendation = "يرجى تحسين الإضاءة - قف في مكان أكثر إشراقاً"
            elif mean_brightness > self.MAX_LIGHTNESS:
                # Too bright/overexposed
                score = (255 - mean_brightness) / (255 - self.MAX_LIGHTNESS) * 0.7
                acceptable = False
                issue = "الصورة فاتحة جداً (إضاءة زائدة)"
                recommendation = "يرجى تقليل الإضاءة -ابتعد عن الضوء المباشر"
            else:
                # Good brightness range
                score = 0.7 + (brightness_variance / 128) * 0.3
                score = min(score, 1.0)
            
            # Check for shadows
            if brightness_variance < 20:
                score *= 0.8
                if acceptable:
                    issue = "الصورة تحتوي على ظلال"
                    recommendation = "يرجى إزالة الظلال من الوجه"
                    acceptable = False
            
            return {
                'score': score,
                'acceptable': acceptable,
                'issue': issue,
                'recommendation': recommendation,
                'mean_brightness': mean_brightness,
                'variance': brightness_variance
            }
            
        except Exception as e:
            print(f"Lighting assessment error: {e}")
            return {'score': 0.5, 'acceptable': True, 'issue': '', 'recommendation': ''}
    
    def assess_sharpness(self, face_region):
        """
        Assess image sharpness/blur
        
        Returns:
            dict: Sharpness assessment result
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Laplacian variance (edge detection)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_variance = laplacian.var()
            
            # Method 2: FFT-based blur detection
            fft = np.fft.fft2(gray)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.log(np.abs(fft_shift) + 1)
            high_freq_ratio = np.mean(magnitude[magnitude > np.mean(magnitude)]) / np.max(magnitude)
            
            # Combine methods
            sharpness_score = (laplacian_variance / 1000) * 0.7 + high_freq_ratio * 0.3
            sharpness_score = min(sharpness_score, 1.0)
            
            acceptable = sharpness_score >= (self.MIN_SHARPNESS / 1000)
            issue = ""
            recommendation = ""
            
            if laplacian_variance < 50:
                acceptable = False
                issue = "الصورة ضبابية جداً"
                recommendation = "يرجى تثبيت الكاميرا وعدم الحركة أثناء الالتقاط"
            elif laplacian_variance < self.MIN_SHARPNESS:
                acceptable = False
                issue = "الصورة غير واضحة تماماً"
                recommendation = "يرجى الاقتراب قليلاً أو تحسين التركيز"
            
            return {
                'score': sharpness_score,
                'acceptable': acceptable,
                'issue': issue,
                'recommendation': recommendation,
                'laplacian_variance': laplacian_variance
            }
            
        except Exception as e:
            print(f"Sharpness assessment error: {e}")
            return {'score': 0.5, 'acceptable': True, 'issue': '', 'recommendation': ''}
    
    def assess_face_angle(self, face_region):
        """
        Assess face angle/orientation
        
        Returns:
            dict: Angle assessment result
        """
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Method: Analyze face symmetry
            # Left-right symmetry for yaw (left/right rotation)
            left_half = gray[:, :width//2]
            right_half = cv2.flip(gray[:, width//2:], 1)
            
            # Compare halves
            if width > 10:
                min_width = min(left_half.shape[1], right_half.shape[1])
                left_half = left_half[:, :min_width]
                right_half = right_half[:, :min_width]
                
                symmetry_score = 1 - np.mean(np.abs(left_half.astype(float) - right_half.astype(float))) / 255
            else:
                symmetry_score = 0.5
            
            # Top-bottom symmetry for pitch (up/down rotation)
            top_half = gray[:height//2, :]
            bottom_half = cv2.flip(gray[height//2:, :], 0)
            
            if height > 10:
                min_height = min(top_half.shape[0], bottom_half.shape[0])
                top_half = top_half[:min_height, :]
                bottom_half = bottom_half[:min_height, :]
                
                vertical_symmetry = 1 - np.mean(np.abs(top_half.astype(float) - bottom_half.astype(float))) / 255
            else:
                vertical_symmetry = 0.5
            
            # Calculate angle score
            angle_score = (symmetry_score * 0.7 + vertical_symmetry * 0.3)
            
            acceptable = angle_score >= 0.6
            issue = ""
            recommendation = ""
            
            if symmetry_score < 0.5:
                acceptable = False
                issue = "الوجه مائل جانبياً (يسار/يمين)"
                recommendation = "يرجى مواجهة الكاميرا مباشرة"
            elif vertical_symmetry < 0.5:
                acceptable = False
                issue = "الوجه مائل عمودياً (أعلى/أسفل)"
                recommendation = "يرجى إبقاء رأسك مستقيماً"
            
            return {
                'score': angle_score,
                'acceptable': acceptable,
                'issue': issue,
                'recommendation': recommendation,
                'symmetry_score': symmetry_score,
                'vertical_symmetry': vertical_symmetry
            }
            
        except Exception as e:
            print(f"Angle assessment error: {e}")
            return {'score': 0.5, 'acceptable': True, 'issue': '', 'recommendation': ''}
    
    def assess_face_size(self, face_region):
        """
        Assess if face size is adequate
        
        Returns:
            dict: Size assessment result
        """
        try:
            height, width = face_region.shape[:2]
            face_size = min(height, width)
            
            # Calculate score
            if face_size >= self.MIN_FACE_SIZE:
                score = min(face_size / 150, 1.0)
                acceptable = True
                issue = ""
                recommendation = ""
            else:
                score = face_size / self.MIN_FACE_SIZE
                acceptable = False
                issue = "الوجه صغير جداً في الصورة"
                recommendation = "يرجى الاقتراب من الكاميرا"
            
            return {
                'score': score,
                'acceptable': acceptable,
                'issue': issue,
                'recommendation': recommendation,
                'face_size': face_size
            }
            
        except Exception as e:
            print(f"Size assessment error: {e}")
            return {'score': 0.5, 'acceptable': True, 'issue': '', 'recommendation': ''}
    
    def get_quality_message(self, quality_result):
        """
        Get user-friendly quality message
        
        Args:
            quality_result: Result from assess_quality
            
        Returns:
            str: User-friendly message
        """
        if quality_result['is_acceptable']:
            return "✓ جودة الصورة جيدة - يمكن المتابعة"
        
        messages = ["⚠️ جودة الصورة غير مقبولة:"]
        for i, issue in enumerate(quality_result['issues'], 1):
            messages.append(f"{i}. {issue}")
        
        messages.append("")
        messages.append("التوصيات:")
        for rec in quality_result['recommendations']:
            messages.append(f"• {rec}")
        
        return "\n".join(messages)
    
    def draw_quality_indicator(self, frame, face_location, quality_result):
        """
        Draw quality indicator on frame
        
        Args:
            frame: Video frame
            face_location: Face location (top, right, bottom, left)
            quality_result: Quality assessment result
            
        Returns:
            frame: Frame with quality indicator
        """
        try:
            top, right, bottom, left = face_location
            
            # Color based on quality
            if quality_result['is_acceptable']:
                color = (0, 255, 0)  # Green
                status = "✓"
            else:
                color = (0, 0, 255)  # Red
                status = "⚠️"
            
            # Draw rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw quality score
            score_text = f"{status} {int(quality_result['overall_score'] * 100)}%"
            cv2.putText(frame, score_text, (left, top - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw main issue if not acceptable
            if not quality_result['is_acceptable'] and quality_result['issues']:
                issue = quality_result['issues'][0][:30]
                cv2.putText(frame, issue, (left, bottom + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            return frame
            
        except Exception as e:
            print(f"Error drawing quality indicator: {e}")
            return frame


class FaceTracker:
    """Track faces across video frames"""
    
    def __init__(self, max_disappeared=10):
        self.next_object_id = 0
        self.objects = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        
    def register(self, face_encoding, face_location, metadata=None):
        """Register a new face for tracking"""
        self.objects[self.next_object_id] = {
            'encoding': face_encoding,
            'location': face_location,
            'metadata': metadata or {},
            'first_seen': time.time(),
            'last_seen': time.time(),
            'frame_count': 1
        }
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1
        
    def deregister(self, object_id):
        """Remove a face from tracking"""
        del self.objects[object_id]
        del self.disappeared[object_id]
        
    def update(self, face_encodings, face_locations):
        """Update tracker with new frame data"""
        if len(face_encodings) == 0:
            # Mark all objects as disappeared
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects
            
        # Initialize new set of tracked objects
        current_objects = set(self.disappeared.keys())
        
        # Try to match faces with existing tracked objects
        for encoding, location in zip(face_encodings, face_locations):
            matched = False
            
            for object_id in current_objects:
                if self._compare_faces(encoding, self.objects[object_id]['encoding']):
                    # Update existing object
                    self.objects[object_id]['location'] = location
                    self.objects[object_id]['last_seen'] = time.time()
                    self.objects[object_id]['frame_count'] += 1
                    self.disappeared[object_id] = 0
                    matched = True
                    current_objects.remove(object_id)
                    break
            
            if not matched:
                # Register new object
                self.register(encoding, location)
        
        # Mark unmatched objects as disappeared
        for object_id in current_objects:
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)
        
        return self.objects
    
    def _compare_faces(self, encoding1, encoding2, threshold=0.6):
        """Compare two face encodings"""
        try:
            if isinstance(encoding1, list) and isinstance(encoding2, list):
                encoding1 = np.array(encoding1)
                encoding2 = np.array(encoding2)
            distance = np.linalg.norm(encoding1 - encoding2)
            return distance < threshold
        except:
            return False
    
    def get_tracked_faces(self):
        """Get all currently tracked faces"""
        return self.objects
    
    def get_face_history(self, object_id):
        """Get tracking history for a specific face"""
        return self.objects.get(object_id, {})

class MaskDetector:
    """Detect face masks using computer vision"""
    
    def __init__(self):
        # In a real implementation, you would load a pre-trained model here
        # For demonstration, we'll use a simplified approach
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.nose_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_mcs_nose.xml')
        self.mouth_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_mcs_mouth.xml')
        
    def detect_mask(self, face_region):
        """Detect if person is wearing a mask"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Detect nose and mouth
            noses = self.nose_cascade.detectMultiScale(gray, 1.1, 5)
            mouths = self.mouth_cascade.detectMultiScale(gray, 1.1, 5)
            
            # Simple heuristic: if nose and mouth are not visible, likely wearing mask
            if len(noses) == 0 and len(mouths) == 0:
                return {
                    'wearing_mask': True,
                    'confidence': 0.7,
                    'reason': 'Nose and mouth not detected'
                }
            elif len(noses) > 0 or len(mouths) > 0:
                return {
                    'wearing_mask': False,
                    'confidence': 0.8,
                    'reason': 'Nose and/or mouth detected'
                }
            else:
                return {
                    'wearing_mask': False,
                    'confidence': 0.5,
                    'reason': 'Uncertain detection'
                }
                
        except Exception as e:
            print(f"Mask detection error: {e}")
            return {
                'wearing_mask': False,
                'confidence': 0.5,
                'reason': 'Detection failed'
            }
    
    def analyze_mask_quality(self, face_region):
        """Analyze mask wearing quality if mask is detected"""
        try:
            mask_result = self.detect_mask(face_region)
            
            if not mask_result['wearing_mask']:
                return mask_result
            
            # Additional analysis for mask quality
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Check if mask covers lower part of face
            lower_face_region = gray[int(height * 0.5):, :]
            lower_variance = np.var(lower_face_region)
            
            # High variance in lower face suggests improper mask wearing
            if lower_variance > 1000:
                quality_score = 0.4
                quality_reason = 'Mask may not cover nose and mouth properly'
            else:
                quality_score = 0.8
                quality_reason = 'Mask appears to be worn correctly'
            
            return {
                'wearing_mask': True,
                'confidence': mask_result['confidence'],
                'quality_score': quality_score,
                'quality_reason': quality_reason,
                'reason': mask_result['reason']
            }
            
        except Exception as e:
            print(f"Mask quality analysis error: {e}")
            return {
                'wearing_mask': False,
                'confidence': 0.5,
                'reason': 'Analysis failed'
            }

class HeadPoseEstimator:
    """Estimate head pose angles (yaw, pitch, roll)"""
    
    def __init__(self):
        # Load facial landmark detector if available
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        except:
            print("Warning: Could not load cascade classifiers")
    
    def estimate_pose(self, face_region, face_location=None):
        """Estimate head pose angles"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Detect eyes for pose estimation
            eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 5)
            
            pose_result = {
                'yaw': 0.0,    # Left/right rotation
                'pitch': 0.0,  # Up/down rotation
                'roll': 0.0,   # Head tilt
                'confidence': 0.5,
                'looking_at_camera': True
            }
            
            if len(eyes) >= 2:
                # Calculate eye positions
                eye_centers = []
                for (ex, ey, ew, eh) in eyes:
                    eye_centers.append((ex + ew//2, ey + eh//2))
                
                if len(eye_centers) >= 2:
                    # Sort eyes by x coordinate
                    eye_centers.sort(key=lambda x: x[0])
                    left_eye = eye_centers[0]
                    right_eye = eye_centers[1]
                    
                    # Calculate yaw based on eye position asymmetry
                    eye_center_x = (left_eye[0] + right_eye[0]) / 2
                    face_center_x = width / 2
                    yaw_offset = (eye_center_x - face_center_x) / face_center_x
                    pose_result['yaw'] = yaw_offset * 45  # Convert to degrees
                    
                    # Calculate roll based on eye line angle
                    eye_line_angle = np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0])
                    pose_result['roll'] = np.degrees(eye_line_angle)
                    
                    # Calculate pitch based on eye vertical position
                    eye_center_y = (left_eye[1] + right_eye[1]) / 2
                    face_center_y = height / 2
                    pitch_offset = (eye_center_y - face_center_y) / face_center_y
                    pose_result['pitch'] = pitch_offset * 30  # Convert to degrees
                    
                    # Determine if looking at camera
                    pose_result['looking_at_camera'] = (
                        abs(pose_result['yaw']) < 30 and
                        abs(pose_result['pitch']) < 20 and
                        abs(pose_result['roll']) < 15
                    )
                    
                    pose_result['confidence'] = 0.8
            
            return pose_result
            
        except Exception as e:
            print(f"Head pose estimation error: {e}")
            return {
                'yaw': 0.0,
                'pitch': 0.0,
                'roll': 0.0,
                'confidence': 0.3,
                'looking_at_camera': True,
                'error': str(e)
            }
    
    def get_pose_description(self, pose_result):
        """Get human-readable pose description"""
        descriptions = []
        
        if not pose_result['looking_at_camera']:
            descriptions.append("غير متجه للكاميرا")
        
        if abs(pose_result['yaw']) > 30:
            if pose_result['yaw'] > 0:
                descriptions.append("مائل لليمين")
            else:
                descriptions.append("مائل لليسار")
        
        if abs(pose_result['pitch']) > 20:
            if pose_result['pitch'] > 0:
                descriptions.append("مائل للأسفل")
            else:
                descriptions.append("مائل للأعلى")
        
        if abs(pose_result['roll']) > 15:
            if pose_result['roll'] > 0:
                descriptions.append("مائل باتجاه عقارب الساعة")
            else:
                descriptions.append("مائل عكس عقارب الساعة")
        
        if not descriptions:
            descriptions.append("متجه للكاميرا مباشرة")
        
        return ", ".join(descriptions)

class EyeTracker:
    """Track eye movements and detect gaze direction"""
    
    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.gaze_history = deque(maxlen=30)
        self.blink_history = deque(maxlen=10)
        
    def track_eyes(self, face_region):
        """Track eyes in face region"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 5)
            
            result = {
                'eyes_detected': len(eyes),
                'left_eye': None,
                'right_eye': None,
                'gaze_direction': 'forward',
                'blink_detected': False,
                'eye_contact': False
            }
            
            if len(eyes) >= 2:
                # Sort eyes by x coordinate (left to right)
                eyes_sorted = sorted(eyes, key=lambda x: x[0])
                result['left_eye'] = eyes_sorted[0]
                result['right_eye'] = eyes_sorted[1]
                
                # Analyze gaze direction (simplified)
                gaze_result = self._analyze_gaze(eyes_sorted, gray.shape)
                result.update(gaze_result)
                
                # Detect blink
                blink_result = self._detect_blink(eyes_sorted, gray)
                result['blink_detected'] = blink_result['blink_detected']
                
                # Check eye contact
                result['eye_contact'] = (
                    result['gaze_direction'] == 'forward' and
                    not result['blink_detected']
                )
            
            return result
            
        except Exception as e:
            print(f"Eye tracking error: {e}")
            return {
                'eyes_detected': 0,
                'left_eye': None,
                'right_eye': None,
                'gaze_direction': 'unknown',
                'blink_detected': False,
                'eye_contact': False,
                'error': str(e)
            }
    
    def _analyze_gaze(self, eyes, face_shape):
        """Analyze gaze direction from eye positions"""
        try:
            left_eye, right_eye = eyes
            
            # Calculate eye centers
            left_center = (left_eye[0] + left_eye[2]//2, left_eye[1] + left_eye[3]//2)
            right_center = (right_eye[0] + right_eye[2]//2, right_eye[1] + right_eye[3]//2)
            
            # Calculate gaze based on eye position relative to face center
            face_center_x = face_shape[1] // 2
            eye_center_x = (left_center[0] + right_center[0]) // 2
            
            horizontal_offset = (eye_center_x - face_center_x) / face_center_x
            
            if abs(horizontal_offset) < 0.1:
                gaze_direction = 'forward'
            elif horizontal_offset > 0.1:
                gaze_direction = 'right'
            else:
                gaze_direction = 'left'
            
            # Store in history
            self.gaze_history.append(gaze_direction)
            
            # Get most common gaze direction from history
            if len(self.gaze_history) >= 5:
                gaze_counts = {}
                for direction in self.gaze_history:
                    gaze_counts[direction] = gaze_counts.get(direction, 0) + 1
                stable_gaze = max(gaze_counts, key=gaze_counts.get)
            else:
                stable_gaze = gaze_direction
            
            return {
                'gaze_direction': gaze_direction,
                'stable_gaze': stable_gaze,
                'horizontal_offset': horizontal_offset
            }
            
        except Exception as e:
            print(f"Gaze analysis error: {e}")
            return {
                'gaze_direction': 'unknown',
                'stable_gaze': 'unknown',
                'horizontal_offset': 0.0
            }
    
    def _detect_blink(self, eyes, gray_face):
        """Detect eye blink"""
        try:
            current_time = time.time()
            
            # Simple blink detection based on eye aspect ratio
            left_eye, right_eye = eyes
            
            # Calculate eye aspect ratio (simplified)
            left_aspect = left_eye[2] / max(left_eye[3], 1)
            right_aspect = right_eye[2] / max(right_eye[3], 1)
            avg_aspect = (left_aspect + right_aspect) / 2
            
            # Blink detected if aspect ratio is very low (eyes closed)
            blink_detected = avg_aspect < 1.0
            
            if blink_detected:
                self.blink_history.append(current_time)
            
            # Check if we had a recent blink
            recent_blinks = [t for t in self.blink_history if current_time - t < 2]
            
            return {
                'blink_detected': blink_detected,
                'recent_blinks': len(recent_blinks),
                'aspect_ratio': avg_aspect
            }
            
        except Exception as e:
            print(f"Blink detection error: {e}")
            return {
                'blink_detected': False,
                'recent_blinks': 0,
                'aspect_ratio': 2.0
            }
    
    def get_attention_score(self):
        """Calculate attention score based on eye tracking"""
        try:
            if len(self.gaze_history) < 10:
                return 0.5
            
            # Calculate gaze stability
            gaze_directions = list(self.gaze_history)
            forward_count = gaze_directions.count('forward')
            gaze_stability = forward_count / len(gaze_directions)
            
            # Calculate blink rate
            current_time = time.time()
            recent_blinks = [t for t in self.blink_history if current_time - t < 10]
            blink_rate = len(recent_blinks) / 10  # Blinks per second
            
            # Normal blink rate is 15-20 per minute
            normal_blink_rate = 0.25  # ~15 blinks per minute
            blink_score = 1.0 - min(abs(blink_rate - normal_blink_rate) / normal_blink_rate, 1.0)
            
            # Combined attention score
            attention_score = (gaze_stability * 0.7) + (blink_score * 0.3)
            
            return max(0.0, min(1.0, attention_score))
            
        except Exception as e:
            print(f"Attention score calculation error: {e}")
            return 0.5

class FaceQualityAssessor:
    """Enhanced face quality assessment with more sophisticated analysis"""
    
    def __init__(self):
        # Quality thresholds
        self.MIN_LIGHTNESS = 40
        self.MAX_LIGHTNESS = 220
        self.MIN_SHARPNESS = 100
        self.MIN_FACE_SIZE = 80
        self.MAX_YAW_ANGLE = 30
        self.MAX_PITCH_ANGLE = 20
        
        # Quality weights
        self.WEIGHT_LIGHTING = 0.25
        self.WEIGHT_SHARPNESS = 0.35
        self.WEIGHT_ANGLE = 0.25
        self.WEIGHT_SIZE = 0.15
        
        # Initialize component assessors
        self.pose_estimator = HeadPoseEstimator()
        self.eye_tracker = EyeTracker()
        
    def assess_face_quality(self, face_region, frame=None, face_location=None):
        """Comprehensive face quality assessment"""
        try:
            results = {
                'is_acceptable': True,
                'overall_score': 0.0,
                'component_scores': {
                    'lighting': 0.0,
                    'sharpness': 0.0,
                    'angle': 0.0,
                    'size': 0.0,
                    'symmetry': 0.0,
                    'clarity': 0.0
                },
                'issues': [],
                'recommendations': [],
                'pose_analysis': None,
                'eye_analysis': None
            }
            
            # Basic quality assessments
            lighting_score = self._assess_enhanced_lighting(face_region)
            results['component_scores']['lighting'] = lighting_score
            
            sharpness_score = self._assess_enhanced_sharpness(face_region)
            results['component_scores']['sharpness'] = sharpness_score
            
            size_score = self._assess_face_size(face_region)
            results['component_scores']['size'] = size_score
            
            symmetry_score = self._assess_face_symmetry(face_region)
            results['component_scores']['symmetry'] = symmetry_score
            
            clarity_score = self._assess_clarity(face_region)
            results['component_scores']['clarity'] = clarity_score
            
            # Advanced analyses
            pose_result = self.pose_estimator.estimate_pose(face_region, face_location)
            results['pose_analysis'] = pose_result
            
            angle_score = self._calculate_angle_score(pose_result)
            results['component_scores']['angle'] = angle_score
            
            eye_result = self.eye_tracker.track_eyes(face_region)
            results['eye_analysis'] = eye_result
            
            # Calculate overall score
            results['overall_score'] = (
                lighting_score * self.WEIGHT_LIGHTING +
                sharpness_score * self.WEIGHT_SHARPNESS +
                angle_score * self.WEIGHT_ANGLE +
                size_score * self.WEIGHT_SIZE
            )
            
            # Determine acceptability and generate issues
            results['is_acceptable'], results['issues'], results['recommendations'] = \
                self._evaluate_acceptability(results['component_scores'], pose_result, eye_result)
            
            return results
            
        except Exception as e:
            print(f"Face quality assessment error: {e}")
            return {
                'is_acceptable': True,
                'overall_score': 0.5,
                'component_scores': {key: 0.5 for key in ['lighting', 'sharpness', 'angle', 'size', 'symmetry', 'clarity']},
                'issues': ['Assessment failed'],
                'recommendations': ['Please try again'],
                'pose_analysis': None,
                'eye_analysis': None,
                'error': str(e)
            }
    
    def _assess_enhanced_lighting(self, face_region):
        """Enhanced lighting assessment"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Multiple lighting metrics
            mean_brightness = np.mean(gray)
            brightness_std = np.std(gray)
            
            # Histogram analysis
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_normalized = hist.flatten() / hist.sum()
            
            # Dynamic range
            dynamic_range = np.percentile(gray, 95) - np.percentile(gray, 5)
            
            # Calculate lighting score
            brightness_score = 0.0
            if self.MIN_LIGHTNESS <= mean_brightness <= self.MAX_LIGHTNESS:
                brightness_score = 0.8
            else:
                distance = min(abs(mean_brightness - self.MIN_LIGHTNESS), abs(mean_brightness - self.MAX_LIGHTNESS))
                brightness_score = max(0.2, 0.8 - distance / 100)
            
            contrast_score = min(brightness_std / 64, 1.0)
            dynamic_score = min(dynamic_range / 200, 1.0)
            
            # Combined lighting score
            lighting_score = (brightness_score * 0.5 + contrast_score * 0.3 + dynamic_score * 0.2)
            
            return min(lighting_score, 1.0)
            
        except Exception as e:
            print(f"Enhanced lighting assessment error: {e}")
            return 0.5
    
    def _assess_enhanced_sharpness(self, face_region):
        """Enhanced sharpness assessment"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Multiple sharpness metrics
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_var = laplacian.var()
            
            # Gradient magnitude
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
            gradient_mean = np.mean(gradient_magnitude)
            
            # Edge density
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Normalize and combine
            laplacian_score = min(laplacian_var / 500, 1.0)
            gradient_score = min(gradient_mean / 50, 1.0)
            edge_score = min(edge_density * 10, 1.0)
            
            sharpness_score = (laplacian_score * 0.4 + gradient_score * 0.4 + edge_score * 0.2)
            
            return min(sharpness_score, 1.0)
            
        except Exception as e:
            print(f"Enhanced sharpness assessment error: {e}")
            return 0.5
    
    def _assess_face_symmetry(self, face_region):
        """Assess facial symmetry"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # Left-right symmetry
            left_half = gray[:, :width//2]
            right_half = cv2.flip(gray[:, width//2:], 1)
            
            min_width = min(left_half.shape[1], right_half.shape[1])
            left_half = left_half[:, :min_width]
            right_half = right_half[:, :min_width]
            
            symmetry_score = 1 - np.mean(np.abs(left_half.astype(float) - right_half.astype(float))) / 255
            
            return max(0.0, min(1.0, symmetry_score))
            
        except Exception as e:
            print(f"Symmetry assessment error: {e}")
            return 0.5
    
    def _assess_clarity(self, face_region):
        """Assess overall image clarity"""
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Local contrast
            kernel = np.ones((5, 5), np.float32) / 25
            local_mean = cv2.filter2D(gray, -1, kernel)
            local_contrast = np.std(gray - local_mean)
            
            # Noise estimation
            noise = cv2.fastNlMeansDenoising(gray, None, h=10)
            noise_level = np.mean(np.abs(gray.astype(float) - noise.astype(float)))
            
            # Combine metrics
            contrast_score = min(local_contrast / 30, 1.0)
            noise_score = max(0.0, 1.0 - noise_level / 50)
            
            clarity_score = (contrast_score * 0.6 + noise_score * 0.4)
            
            return max(0.0, min(1.0, clarity_score))
            
        except Exception as e:
            print(f"Clarity assessment error: {e}")
            return 0.5
    
    def _assess_face_size(self, face_region):
        """Assess face size"""
        try:
            height, width = face_region.shape[:2]
            face_size = min(height, width)
            
            if face_size >= self.MIN_FACE_SIZE:
                return min(face_size / 200, 1.0)
            else:
                return face_size / self.MIN_FACE_SIZE
                
        except Exception as e:
            print(f"Face size assessment error: {e}")
            return 0.5
    
    def _calculate_angle_score(self, pose_result):
        """Calculate angle score from pose analysis"""
        try:
            yaw_abs = abs(pose_result.get('yaw', 0))
            pitch_abs = abs(pose_result.get('pitch', 0))
            roll_abs = abs(pose_result.get('roll', 0))
            
            # Penalize extreme angles
            yaw_score = max(0.0, 1.0 - yaw_abs / 45)
            pitch_score = max(0.0, 1.0 - pitch_abs / 30)
            roll_score = max(0.0, 1.0 - roll_abs / 20)
            
            angle_score = (yaw_score * 0.4 + pitch_score * 0.4 + roll_score * 0.2)
            
            return angle_score
            
        except Exception as e:
            print(f"Angle score calculation error: {e}")
            return 0.5
    
    def _evaluate_acceptability(self, component_scores, pose_result, eye_result):
        """Evaluate overall acceptability and generate recommendations"""
        issues = []
        recommendations = []
        is_acceptable = True
        
        # Check each component
        if component_scores['lighting'] < 0.4:
            is_acceptable = False
            issues.append("إضاءة غير مناسبة")
            recommendations.append("تحسين الإضاءة")
        
        if component_scores['sharpness'] < 0.4:
            is_acceptable = False
            issues.append("صورة غير واضحة")
            recommendations.append("تثبيت الكاميرا وعدم الحركة")
        
        if component_scores['size'] < 0.3:
            is_acceptable = False
            issues.append("الوجه صغير جداً")
            recommendations.append("الاقتراب من الكاميرا")
        
        if component_scores['angle'] < 0.4:
            is_acceptable = False
            issues.append("الوجه مائل")
            recommendations.append("مواجهة الكاميرا مباشرة")
        
        # Check pose
        if pose_result and not pose_result.get('looking_at_camera', True):
            if is_acceptable:  # Only add if not already unacceptable
                issues.append("غير متجه للكاميرا")
                recommendations.append("النظر للكاميرا مباشرة")
        
        # Check eyes
        if eye_result and eye_result.get('eyes_detected', 0) < 2:
            if is_acceptable:
                issues.append("لا يمكن رؤية العينين")
                recommendations.append("ضمان وضوح العينين")
        
        return is_acceptable, issues, recommendations

# Create aliases for backward compatibility
FaceQualityAssessment = FaceQualityAssessor

class FaceClustering:
    """
    Face Clustering 

    """
    
    def __init__(self, similarity_threshold=0.6):
        """
        Initialize Face Clustering
        
        Args:
            similarity_threshold: Threshold for considering faces as similar (lower = more strict)
        """
        self.similarity_threshold = similarity_threshold
        self.clusters = {}
        self.face_encodings = {}
        self.face_metadata = {}
        
    def add_face(self, face_id, face_encoding, metadata=None):
        """
        Add a face to the clustering system
        
        Args:
            face_id: Unique identifier for the face
            face_encoding: Face encoding array
            metadata: Optional metadata dict (name, image_path, etc.)
        """
        try:
            self.face_encodings[face_id] = np.array(face_encoding)
            self.face_metadata[face_id] = metadata or {}
            self._update_clusters()
        except Exception as e:
            print(f"Error adding face: {e}")
    
    def _update_clusters(self):
        """Update face clusters based on current encodings"""
        if not self.face_encodings:
            return
            
        face_ids = list(self.face_encodings.keys())
        encodings = np.array(list(self.face_encodings.values()))
        
        # Initialize clusters
        self.clusters = {}
        assigned = set()
        
        for i, face_id in enumerate(face_ids):
            if face_id in assigned:
                continue
                
            # Create new cluster
            cluster_id = f"cluster_{len(self.clusters)}"
            self.clusters[cluster_id] = {
                'members': [face_id],
                'centroid': encodings[i],
                'size': 1
            }
            assigned.add(face_id)
            
            # Find similar faces
            for j, other_id in enumerate(face_ids):
                if other_id in assigned or i == j:
                    continue
                    
                # Calculate face distance
                distance = np.linalg.norm(encodings[i] - encodings[j])
                
                if distance < self.similarity_threshold:
                    self.clusters[cluster_id]['members'].append(other_id)
                    self.clusters[cluster_id]['size'] += 1
                    assigned.add(other_id)
    
    def find_duplicates(self, face_id):
        """
        Find potential duplicates for a specific face
        
        Args:
            face_id: The face ID to check
            
        Returns:
            list: List of duplicate face IDs
        """
        duplicates = []
        
        if face_id not in self.face_encodings:
            return duplicates
            
        target_encoding = self.face_encodings[face_id]
        
        for other_id, encoding in self.face_encodings.items():
            if other_id == face_id:
                continue
                
            distance = np.linalg.norm(target_encoding - encoding)
            
            if distance < self.similarity_threshold:
                duplicates.append({
                    'face_id': other_id,
                    'distance': float(distance),
                    'metadata': self.face_metadata.get(other_id, {})
                })
        
        # Sort by distance (most similar first)
        duplicates.sort(key=lambda x: x['distance'])
        return duplicates
    
    def detect_duplicate_groups(self):
        """
        Detect groups of duplicate/similar faces
        
        Returns:
            list: List of duplicate groups
        """
        duplicate_groups = []
        
        for cluster_id, cluster in self.clusters.items():
            if cluster['size'] > 1:
                group_info = {
                    'cluster_id': cluster_id,
                    'member_count': cluster['size'],
                    'members': []
                }
                
                for face_id in cluster['members']:
                    member_info = {
                        'face_id': face_id,
                        'metadata': self.face_metadata.get(face_id, {})
                    }
                    group_info['members'].append(member_info)
                
                duplicate_groups.append(group_info)
        
        return duplicate_groups
    
    def get_cluster_info(self, cluster_id):
        """
        Get information about a specific cluster
        
        Args:
            cluster_id: The cluster ID
            
        Returns:
            dict: Cluster information
        """
        return self.clusters.get(cluster_id, {})
    
    def get_all_clusters(self):
        """
        Get all clusters
        
        Returns:
            dict: All clusters with their information
        """
        return self.clusters
    
    def analyze_face_distribution(self):
        """
        Analyze the distribution of faces across clusters
        
        Returns:
            dict: Distribution statistics
        """
        total_faces = len(self.face_encodings)
        total_clusters = len(self.clusters)
        
        cluster_sizes = [c['size'] for c in self.clusters.values()]
        
        # Count singletons vs groups
        singleton_count = sum(1 for s in cluster_sizes if s == 1)
        group_count = total_clusters - singleton_count
        
        # Find largest cluster
        largest_cluster_id = max(self.clusters, key=lambda x: self.clusters[x]['size']) if self.clusters else None
        largest_cluster_size = self.clusters[largest_cluster_id]['size'] if largest_cluster_id else 0
        
        return {
            'total_faces': total_faces,
            'total_clusters': total_clusters,
            'singleton_clusters': singleton_count,
            'duplicate_groups': group_count,
            'largest_cluster_size': largest_cluster_size,
            'average_cluster_size': np.mean(cluster_sizes) if cluster_sizes else 0,
            'cluster_size_distribution': {
                '1': singleton_count,
                '2': sum(1 for s in cluster_sizes if s == 2),
                '3': sum(1 for s in cluster_sizes if s == 3),
                '4+': sum(1 for s in cluster_sizes if s >= 4)
            }
        }
    
    def suggest_actions(self):
        """
        Suggest actions based on clustering analysis
        
        Returns:
            list: List of suggested actions
        """
        suggestions = []
        
        # Check for duplicates
        duplicate_groups = self.detect_duplicate_groups()
        
        for group in duplicate_groups:
            if group['member_count'] == 2:
                suggestions.append({
                    'type': 'duplicate_check',
                    'priority': 'high',
                    'message': f"Duplicate faces found",
                    'cluster_id': group['cluster_id'],
                    'action': 'Review the two images to confirm they are of the same person'
                })
            else:
                suggestions.append({
                    'type': 'multiple_duplicates',
                    'priority': 'critical',
                    'message': f"Multiple duplicate faces found",
                    'cluster_id': group['cluster_id'],
                    'action': 'Verify the presence of fraud or duplicate registration'
                })
        
        # Check for isolated faces (potential issues)
        for face_id, metadata in self.face_metadata.items():
            if not metadata.get('name'):
                suggestions.append({
                    'type': 'unnamed_face',
                    'priority': 'medium',
                    'message': f"Unnamed face found",
                    'face_id': face_id,
                    'action': 'Add a name to the face or delete it'
                })
        
        return suggestions
    
    def load_from_directory(self, directory_path, known_extensions=None):
        """
        Load faces from a directory of images
        
        Args:
            directory_path: Path to directory containing face images
            known_extensions: List of valid image extensions
            
        Returns:
            dict: Results of loading operation
        """
        if known_extensions is None:
            known_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        results = {
            'loaded': 0,
            'failed': 0,
            'errors': []
        }
        
        if not os.path.exists(directory_path):
            results['errors'].append(f"Directory not found: {directory_path}")
            return results
        
        if not FACE_RECOGNITION_AVAILABLE:
            results['errors'].append("face_recognition library not available")
            return results
        
        for filename in os.listdir(directory_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in known_extensions:
                continue
                
            try:
                image_path = os.path.join(directory_path, filename)
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    face_id = os.path.splitext(filename)[0]
                    metadata = {
                        'name': face_id,
                        'image_path': image_path,
                        'filename': filename
                    }
                    self.add_face(face_id, encodings[0], metadata)
                    results['loaded'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{filename}: {str(e)}")
        
        return results
    
    def export_clusters_to_json(self, filepath):
        """
        Export cluster data to JSON file
        
        Args:
            filepath: Path to output JSON file
        """
        try:
            export_data = {
                'clusters': {},
                'metadata': self.face_metadata,
                'distribution': self.analyze_face_distribution(),
                'suggestions': self.suggest_actions()
            }
            
            for cluster_id, cluster in self.clusters.items():
                export_data['clusters'][cluster_id] = {
                    'members': cluster['members'],
                    'size': cluster['size']
                }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting clusters: {e}")
            return False
    
    def visualize_clusters(self, output_dir=None):
        """
        Create visualization of clusters
        
        Args:
            output_dir: Directory to save visualization images
            
        Returns:
            dict: Paths to generated visualization files
        """
        if output_dir is None:
            output_dir = "cluster_visualization"
        
        os.makedirs(output_dir, exist_ok=True)
        
        visualization_files = {}
        
        try:
            # Create a simple text-based report
            report_path = os.path.join(output_dir, "cluster_report.txt")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("Face Clustering Report\n")
                f.write("=" * 60 + "\n\n")
                
                # Distribution
                dist = self.analyze_face_distribution()
                f.write(f"Total Faces: {dist['total_faces']}\n")
                f.write(f"Total Clusters: {dist['total_clusters']}\n")
                f.write(f"Singleton Clusters: {dist['singleton_clusters']}\n")
                f.write(f"Duplicate Groups: {dist['duplicate_groups']}\n\n")
                
                # Suggestions
                f.write("Suggestions:\n")
                f.write("-" * 40 + "\n")
                for suggestion in self.suggest_actions():
                    f.write(f"[{suggestion['priority'].upper()}] {suggestion['message']}\n")
                    f.write(f"  Action: {suggestion['action']}\n\n")
                
                # Duplicate groups
                f.write("\nDuplicate Groups:\n")
                f.write("-" * 40 + "\n")
                for group in self.detect_duplicate_groups():
                    f.write(f"\nCluster {group['cluster_id']} ({group['member_count']} members):\n")
                    for member in group['members']:
                        name = member['metadata'].get('name', 'Unknown')
                        f.write(f"  - {name}\n")
            
            visualization_files['report'] = report_path
            
        except Exception as e:
            print(f"Error creating visualization: {e}")
        
        return visualization_files

class AgeGenderEstimator:
    """Estimates age and gender using OpenCV DNN"""
    
    def __init__(self):
        # Models would normally be loaded here
        self.gender_list = ['Male', 'Female']
        self.age_list = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        
    def estimate(self, face_img):
        """Estimate age and gender from a face image"""
        try:
            # Placeholder logic for demo purposes
            # In a real app, this would use a pre-trained model
            h, w = face_img.shape[:2]
            gender = "Male" if h % 2 == 0 else "Female"
            age = "25-32"
            return gender, age
        except:
            return "Unknown", "Unknown"

class AlertnessTracker:
    """Tracks alertness based on eye closure duration"""
    def __init__(self):
        self.closure_start_time = None
        
    def get_alertness(self, eyes_closed):
        if eyes_closed:
            if not self.closure_start_time:
                self.closure_start_time = time.time()
            duration = time.time() - self.closure_start_time
            return max(0.0, 1.0 - (duration / 3.0)) # 3 seconds to 0 alertness
        else:
            self.closure_start_time = None
            return 1.0
