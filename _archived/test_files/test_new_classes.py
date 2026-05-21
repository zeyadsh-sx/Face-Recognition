#!/usr/bin/env python3
"""
Test script for new AI features classes
"""

import cv2
import numpy as np
from features_ai_advanced import (
    FaceTracker, MaskDetector, HeadPoseEstimator, 
    EyeTracker, FaceQualityAssessor, FaceClustering
)

def test_new_classes():
    """Test all new classes with sample data"""
    
    print("=" * 60)
    print("Testing New AI Features Classes")
    print("=" * 60)
    
    # Create a sample face region (dummy image)
    sample_face = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    
    # Test 1: FaceTracker
    print("\n1. Testing FaceTracker:")
    tracker = FaceTracker()
    
    # Simulate face encodings and locations
    face_encodings = [np.random.rand(128) for _ in range(2)]
    face_locations = [(50, 150, 150, 50), (60, 160, 160, 60)]
    
    tracked_faces = tracker.update(face_encodings, face_locations)
    print(f"   Tracked faces: {len(tracked_faces)}")
    print(f"   Face IDs: {list(tracked_faces.keys())}")
    
    # Test 2: MaskDetector
    print("\n2. Testing MaskDetector:")
    mask_detector = MaskDetector()
    mask_result = mask_detector.detect_mask(sample_face)
    print(f"   Wearing mask: {mask_result['wearing_mask']}")
    print(f"   Confidence: {mask_result['confidence']:.2f}")
    print(f"   Reason: {mask_result['reason']}")
    
    # Test 3: HeadPoseEstimator
    print("\n3. Testing HeadPoseEstimator:")
    pose_estimator = HeadPoseEstimator()
    pose_result = pose_estimator.estimate_pose(sample_face)
    print(f"   Yaw: {pose_result['yaw']:.1f}°")
    print(f"   Pitch: {pose_result['pitch']:.1f}°")
    print(f"   Roll: {pose_result['roll']:.1f}°")
    print(f"   Looking at camera: {pose_result['looking_at_camera']}")
    print(f"   Pose description: {pose_estimator.get_pose_description(pose_result)}")
    
    # Test 4: EyeTracker
    print("\n4. Testing EyeTracker:")
    eye_tracker = EyeTracker()
    eye_result = eye_tracker.track_eyes(sample_face)
    print(f"   Eyes detected: {eye_result['eyes_detected']}")
    print(f"   Gaze direction: {eye_result['gaze_direction']}")
    print(f"   Blink detected: {eye_result['blink_detected']}")
    print(f"   Eye contact: {eye_result['eye_contact']}")
    print(f"   Attention score: {eye_tracker.get_attention_score():.2f}")
    
    # Test 5: FaceQualityAssessor
    print("\n5. Testing FaceQualityAssessor:")
    quality_assessor = FaceQualityAssessor()
    quality_result = quality_assessor.assess_face_quality(sample_face)
    print(f"   Overall quality score: {quality_result['overall_score']:.2f}")
    print(f"   Is acceptable: {quality_result['is_acceptable']}")
    print(f"   Component scores:")
    for component, score in quality_result['component_scores'].items():
        print(f"     {component}: {score:.2f}")
    
    if quality_result['issues']:
        print(f"   Issues: {', '.join(quality_result['issues'])}")
    if quality_result['recommendations']:
        print(f"   Recommendations: {', '.join(quality_result['recommendations'])}")
    
    # Test 6: FaceClustering
    print("\n6. Testing FaceClustering:")
    clustering = FaceClustering()
    
    # Add some sample faces
    for i in range(5):
        face_id = f"person_{i}"
        face_encoding = np.random.rand(128)
        metadata = {'name': f'Person {i}', 'image_path': f'{face_id}.jpg'}
        clustering.add_face(face_id, face_encoding, metadata)
    
    # Analyze clusters
    distribution = clustering.analyze_face_distribution()
    print(f"   Total faces: {distribution['total_faces']}")
    print(f"   Total clusters: {distribution['total_clusters']}")
    print(f"   Singleton clusters: {distribution['singleton_clusters']}")
    print(f"   Duplicate groups: {distribution['duplicate_groups']}")
    
    # Get suggestions
    suggestions = clustering.suggest_actions()
    if suggestions:
        print(f"   Suggestions:")
        for suggestion in suggestions:
            print(f"     - [{suggestion['priority'].upper()}] {suggestion['message']}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_new_classes()
