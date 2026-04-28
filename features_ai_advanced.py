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

class FaceTracker:
    """Track faces across frames using centroid tracking and disappearance logic"""

    def __init__(self, max_disappeared=10, max_distance=80):
        self.next_face_id = 0
        self.tracks = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    @staticmethod
    def _distance(point_a, point_b):
        return np.linalg.norm(np.array(point_a) - np.array(point_b))

    def update(self, detections):
        """Update tracked faces and assign IDs to current detections"""
        current_centers = [
            (int(x + w / 2), int(y + h / 2))
            for (x, y, w, h) in detections
        ]

        if len(self.tracks) == 0:
            for center, box in zip(current_centers, detections):
                self.tracks[self.next_face_id] = {
                    'center': center,
                    'box': box,
                    'disappeared': 0,
                    'last_seen': datetime.now()
                }
                self.next_face_id += 1
            return self.tracks

        existing_ids = list(self.tracks.keys())
        existing_centers = [self.tracks[_id]['center'] for _id in existing_ids]

        matches = []
        unmatched_new = set(range(len(current_centers)))
        unmatched_existing = set(existing_ids)

        # Greedy matching by nearest distance
        for idx_new, center in enumerate(current_centers):
            best_match = None
            best_distance = self.max_distance + 1
            for existing_id in list(unmatched_existing):
                dist = self._distance(center, self.tracks[existing_id]['center'])
                if dist < best_distance:
                    best_distance = dist
                    best_match = existing_id
            if best_match is not None and best_distance <= self.max_distance:
                matches.append((best_match, idx_new))
                unmatched_existing.discard(best_match)
                unmatched_new.discard(idx_new)

        updated_tracks = {}
        for existing_id, track in self.tracks.items():
            if any(existing_id == match[0] for match in matches):
                match_idx = next(match[1] for match in matches if match[0] == existing_id)
                updated_tracks[existing_id] = {
                    'center': current_centers[match_idx],
                    'box': detections[match_idx],
                    'disappeared': 0,
                    'last_seen': datetime.now()
                }
            else:
                track['disappeared'] += 1
                if track['disappeared'] <= self.max_disappeared:
                    updated_tracks[existing_id] = track

        for idx_new in unmatched_new:
            self.tracks[self.next_face_id] = {
                'center': current_centers[idx_new],
                'box': detections[idx_new],
                'disappeared': 0,
                'last_seen': datetime.now()
            }
            self.next_face_id += 1

        self.tracks = {**updated_tracks, **{
            id_: track for id_, track in self.tracks.items() if id_ not in updated_tracks
        }}

        return self.tracks


class PresenceManager:
    """Manage student entry, exit, and duration within a lecture session"""

    def __init__(self, exit_timeout=8, db=None, lecture_id=None):
        self.exit_timeout = exit_timeout
        self.db = db
        self.lecture_id = lecture_id
        self.active_presence = {}
        self.closed_presence = []

    def set_lecture(self, lecture_id):
        self.lecture_id = lecture_id

    def update_presence(self, recognized_face, timestamp=None):
        if recognized_face.get('student_id') is None:
            return None

        timestamp = timestamp or datetime.now()
        student_id = recognized_face['student_id']
        name = recognized_face.get('name', 'Unknown')
        emotion_data = recognized_face.get('emotion_data', {})

        current = self.active_presence.get(student_id)
        mask_detected = recognized_face.get('mask_detected')
        mask_confidence = recognized_face.get('mask_confidence')
        mask_violation = recognized_face.get('mask_violation', False)

        head_pose = recognized_face.get('head_pose')
        attention_score = recognized_face.get('attention_score')
        gaze_direction = recognized_face.get('gaze_direction')
        blink_score = recognized_face.get('blink_score')

        if current is None or current.get('status') == 'left':
            current = {
                'student_id': student_id,
                'name': name,
                'entry_time': timestamp,
                'last_seen': timestamp,
                'status': 'present',
                'emotion': emotion_data.get('emotion', 'neutral'),
                'emotion_confidence': emotion_data.get('confidence', 0.0),
                'head_pose': head_pose,
                'attention_score': attention_score,
                'gaze_direction': gaze_direction,
                'blink_score': blink_score,
                'mask_detected': mask_detected,
                'mask_confidence': mask_confidence,
                'mask_violation': mask_violation
            }
        else:
            current['last_seen'] = timestamp
            current['emotion'] = emotion_data.get('emotion', current['emotion'])
            current['emotion_confidence'] = emotion_data.get('confidence', current['emotion_confidence'])
            current['head_pose'] = head_pose or current.get('head_pose')
            current['attention_score'] = attention_score if attention_score is not None else current.get('attention_score')
            current['gaze_direction'] = gaze_direction or current.get('gaze_direction')
            current['blink_score'] = blink_score if blink_score is not None else current.get('blink_score')
            current['mask_detected'] = mask_detected if mask_detected is not None else current.get('mask_detected')
            current['mask_confidence'] = mask_confidence if mask_confidence is not None else current.get('mask_confidence')
            current['mask_violation'] = current.get('mask_violation', False) or mask_violation

        self.active_presence[student_id] = current

        if self.db and self.lecture_id:
            self.db.create_or_update_lecture_presence(
                self.lecture_id,
                student_id,
                current['entry_time'].time(),
                current['emotion'],
                current['emotion_confidence'],
                current.get('head_pose'),
                current.get('attention_score'),
                current.get('gaze_direction'),
                current.get('blink_score'),
                current['mask_detected'],
                current['mask_confidence'],
                current['mask_violation']
            )

        return current

    def close_inactive(self, timestamp=None):
        timestamp = timestamp or datetime.now()
        closed = []
        for student_id, record in list(self.active_presence.items()):
            if record['status'] == 'present':
                elapsed = (timestamp - record['last_seen']).total_seconds()
                if elapsed > self.exit_timeout:
                    exit_time = record['last_seen']
                    duration_seconds = int((exit_time - record['entry_time']).total_seconds())
                    duration_str = str(timedelta(seconds=max(duration_seconds, 0)))
                    record.update({
                        'exit_time': exit_time,
                        'duration_seconds': duration_seconds,
                        'duration': duration_str,
                        'status': 'left'
                    })
                    closed.append(record)
                    self.active_presence.pop(student_id, None)

                    if self.db and self.lecture_id:
                        self.db.close_lecture_presence(
                            self.lecture_id,
                            student_id,
                            exit_time.time()
                        )

        self.closed_presence.extend(closed)
        return closed

    def finalize_all(self, timestamp=None):
        timestamp = timestamp or datetime.now()
        for student_id in list(self.active_presence.keys()):
            record = self.active_presence[student_id]
            self.close_inactive(timestamp)

    def get_active_presence(self):
        return list(self.active_presence.values())

    def get_closed_presence(self):
        return list(self.closed_presence)


class MultiFaceAttendanceSystem:
    """Advanced multi-face recognition system with per-student session tracking"""

    def __init__(self, db=None, lecture_id=None, tolerance=0.5, exit_timeout=8):
        self.db = db
        self.lecture_id = lecture_id
        self.tolerance = tolerance
        self.face_tracker = FaceTracker(max_disappeared=12, max_distance=100)
        self.presence_manager = PresenceManager(exit_timeout=exit_timeout, db=db, lecture_id=lecture_id)
        self.emotion_detector = EmotionDetector()
        self.mask_detector = MaskDetector()
        self.head_pose_estimator = HeadPoseEstimator()
        self.eye_tracker = EyeTracker()
        self.known_students = []
        self.known_encodings = []
        self.known_ids = []
        self.known_names = []

        if self.db:
            self.load_known_students()

    def set_lecture_id(self, lecture_id):
        self.lecture_id = lecture_id
        self.presence_manager.set_lecture(lecture_id)

    def load_known_students(self):
        self.known_students = self.db.get_all_students() if self.db else []
        self.known_encodings = [s['face_encoding'] for s in self.known_students if s['face_encoding'] is not None]
        self.known_ids = [s['id'] for s in self.known_students if s['face_encoding'] is not None]
        self.known_names = [s['name'] for s in self.known_students if s['face_encoding'] is not None]

    def recognize_faces(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = []

        detections = []
        if FACE_RECOGNITION_AVAILABLE:
            locations = face_recognition.face_locations(rgb_frame, model='hog')
            encodings = face_recognition.face_encodings(rgb_frame, locations)

            for location, encoding in zip(locations, encodings):
                top, right, bottom, left = location
                x, y, w, h = left, top, right - left, bottom - top
                detections.append((x, y, w, h))

                student_id = None
                student_name = 'Unknown'
                if self.known_encodings:
                    distances = face_recognition.face_distance(self.known_encodings, encoding)
                    best_index = int(np.argmin(distances)) if len(distances) > 0 else None
                    if best_index is not None and distances[best_index] <= self.tolerance:
                        student_id = self.known_ids[best_index]
                        student_name = self.known_names[best_index]

                face_region = frame[y:y + h, x:x + w]
                emotion_data = self.emotion_detector.detect_emotion(face_region)
                mask_detected, mask_confidence = self.mask_detector.detect_mask(face_region)
                mask_violation = mask_detected is False
                head_pose = self.head_pose_estimator.estimate_pose(face_region)
                eye_data = self.eye_tracker.track_eyes(face_region)
                attention_score = self.calculate_attention_score(head_pose, eye_data, mask_detected)

                results.append({
                    'student_id': student_id,
                    'name': student_name,
                    'bounding_box': (x, y, w, h),
                    'emotion_data': emotion_data,
                    'face_encoding': encoding,
                    'face_region': face_region,
                    'head_pose': head_pose,
                    'attention_score': attention_score,
                    'gaze_direction': eye_data.get('gaze_direction'),
                    'blink_score': eye_data.get('blink_score', 0.0),
                    'mask_detected': mask_detected,
                    'mask_confidence': mask_confidence,
                    'mask_violation': mask_violation
                })
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            detections = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

            for (x, y, w, h) in detections:
                face_region = frame[y:y + h, x:x + w]
                emotion_data = self.emotion_detector.detect_emotion(face_region)
                mask_detected, mask_confidence = self.mask_detector.detect_mask(face_region)
                mask_violation = mask_detected is False
                head_pose = self.head_pose_estimator.estimate_pose(face_region)
                eye_data = self.eye_tracker.track_eyes(face_region)
                attention_score = self.calculate_attention_score(head_pose, eye_data, mask_detected)

                results.append({
                    'student_id': None,
                    'name': 'Unknown',
                    'bounding_box': (x, y, w, h),
                    'emotion_data': emotion_data,
                    'face_encoding': None,
                    'face_region': face_region,
                    'head_pose': head_pose,
                    'attention_score': attention_score,
                    'gaze_direction': eye_data.get('gaze_direction'),
                    'blink_score': eye_data.get('blink_score', 0.0),
                    'mask_detected': mask_detected,
                    'mask_confidence': mask_confidence,
                    'mask_violation': mask_violation
                })

        return results

    def calculate_attention_score(self, head_pose, eye_data, mask_detected):
        """Calculate normalized attention score based on head pose, eye gaze, and mask compliance"""
        score = 0.0
        score += 0.35 if head_pose.get('is_facing_forward') else 0.0
        score += 0.25 if eye_data.get('gaze_direction') == 'center' else 0.0
        score += min(max(eye_data.get('blink_score', 0.0), 0.0), 1.0) * 0.25
        score += 0.15 if mask_detected else 0.0
        return min(max(score, 0.0), 1.0)

    def process_frame(self, frame):
        timestamp = datetime.now()
        recognized_faces = self.recognize_faces(frame)
        detections = [face['bounding_box'] for face in recognized_faces]
        tracked_faces = self.face_tracker.update(detections)

        for face in recognized_faces:
            self.presence_manager.update_presence(face, timestamp)

        self.presence_manager.close_inactive(timestamp)
        return recognized_faces, tracked_faces

    def annotate_frame(self, frame, recognized_faces, tracked_faces):
        for face in recognized_faces:
            x, y, w, h = face['bounding_box']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 155, 255), 2)
            name = face['name']
            emotion = face['emotion_data'].get('emotion', 'neutral')
            mask_label = 'Mask' if face.get('mask_detected') else 'No Mask'
            attention_score = face.get('attention_score')
            attention_label = f"Attention:{attention_score:.2f}" if attention_score is not None else "Attention:NA"
            label = f"{name} | {emotion} | {mask_label} | {attention_label}"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        for face_id, track in tracked_faces.items():
            x, y, w, h = track['box']
            cv2.putText(frame, f"ID:{face_id}", (x, y + h + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)

        return frame

    def get_active_students(self):
        return self.presence_manager.get_active_presence()

    def get_closed_students(self):
        return self.presence_manager.get_closed_presence()


class MaskDetector:
    """Detect if a person is wearing a face mask (basic placeholder)"""
    
    def __init__(self):
        pass
    
    def detect_mask(self, face_region):
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            lower_half = gray[gray.shape[0]//2:, :]
            
            variance = np.var(lower_half)
            
            if variance < 500:
                return True, 0.8  # Mask likely
            return False, 0.7
        
        except Exception:
            return False, 0.5


class AgeGenderEstimator:
    """Estimate age and gender (placeholder for future deep learning model)"""
    
    def __init__(self):
        self.genders = ['male', 'female']
    
    def estimate(self, face_region):
        try:
            age = np.random.randint(18, 35)
            gender = np.random.choice(self.genders)
            confidence = np.random.uniform(0.5, 0.9)
            
            return {
                'age': age,
                'gender': gender,
                'confidence': confidence
            }
        
        except Exception:
            return {
                'age': None,
                'gender': None,
                'confidence': 0.0
            }


class HeadPoseEstimator:
    """Estimate head pose (simplified)"""
    
    def __init__(self):
        pass
    
    def estimate_pose(self, face_region):
        try:
            h, w = face_region.shape[:2]
            
            yaw = np.random.uniform(-15, 15)
            pitch = np.random.uniform(-10, 10)
            roll = np.random.uniform(-5, 5)
            
            return {
                'yaw': yaw,
                'pitch': pitch,
                'roll': roll,
                'is_facing_forward': abs(yaw) < 10 and abs(pitch) < 10
            }
        
        except Exception:
            return {
                'yaw': 0,
                'pitch': 0,
                'roll': 0,
                'is_facing_forward': True
            }


class EyeTracker:
    """Track eye gaze direction"""
    
    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    def track_eyes(self, face_region):
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 5)
            
            gaze = "center"
            if len(eyes) >= 2:
                gaze = np.random.choice(["left", "right", "center"])
            blink_score = 0.7 if len(eyes) >= 2 else 0.3

            return {
                'eyes_detected': len(eyes),
                'gaze_direction': gaze,
                'blink_score': blink_score
            }
        
        except Exception:
            return {
                'eyes_detected': 0,
                'gaze_direction': 'unknown',
                'blink_score': 0.3
            }


class FaceQualityAssessor:
    """Assess quality of detected face"""
    
    def __init__(self):
        pass
    
    def assess(self, face_region):
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            brightness = np.mean(gray)
            
            quality_score = (min(blur / 100, 1.0) * 0.6) + (min(brightness / 255, 1.0) * 0.4)
            
            return {
                'blur_score': blur,
                'brightness': brightness,
                'quality_score': quality_score,
                'is_good_quality': quality_score > 0.5
            }
        
        except Exception:
            return {
                'quality_score': 0.5,
                'is_good_quality': True
            }


class FaceClustering:
    """Cluster similar faces using encodings"""
    
    def __init__(self):
        self.clusters = []
    
    def cluster_faces(self, encodings, threshold=0.6):
        try:
            clusters = []
            
            for encoding in encodings:
                placed = False
                
                for cluster in clusters:
                    distances = [np.linalg.norm(encoding - e) for e in cluster]
                    if np.mean(distances) < threshold:
                        cluster.append(encoding)
                        placed = True
                        break
                
                if not placed:
                    clusters.append([encoding])
            
            self.clusters = clusters
            return clusters
        
        except Exception:
            return []

