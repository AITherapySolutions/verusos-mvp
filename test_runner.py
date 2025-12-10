#!/usr/bin/env python3
"""
Test runner for VerusOS Detection Engine v2.0
Validates detection accuracy against test set
"""

import csv
from app.core.detection import detector

def load_test_set(filename="test_set_v1.csv"):
    """Load test cases from CSV"""
    test_cases = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append({
                'message': row['message'],
                'expected_category': row['expected_category'],
                'subtype': row['subtype']
            })
    return test_cases

def categorize_detection(result):
    """Map detection result to category"""
    if result.risk_tier == "BASELINE":
        return "SAFE"
    elif result.crisis_detected:
        return "CRISIS"
    elif result.grooming_detected:
        return "GROOMING"
    elif result.violence_detected:
        return "VIOLENCE"
    return "UNKNOWN"

def run_tests(test_cases):
    """Run all test cases and report results"""
    
    results = {
        'total': len(test_cases),
        'passed': 0,
        'failed': 0,
        'by_category': {
            'CRISIS': {'total': 0, 'passed': 0, 'failed': 0},
            'GROOMING': {'total': 0, 'passed': 0, 'failed': 0},
            'VIOLENCE': {'total': 0, 'passed': 0, 'failed': 0},
            'SAFE': {'total': 0, 'passed': 0, 'failed': 0},
        },
        'failures': []
    }
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case['message']
        expected = test_case['expected_category']
        
        # Run detection
        detection_result = detector.detect(message)
        detected = categorize_detection(detection_result)
        
        # Track results
        results['by_category'][expected]['total'] += 1
        
        # Check if correct
        is_correct = (detected == expected)
        
        if is_correct:
            results['passed'] += 1
            results['by_category'][expected]['passed'] += 1
        else:
            results['failed'] += 1
            results['by_category'][expected]['failed'] += 1
            results['failures'].append({
                'message': message,
                'expected': expected,
                'detected': detected,
                'score': detection_result.risk_score,
                'tier': detection_result.risk_tier
            })
    
    return results

def print_results(results):
    """Print test results"""
    
    total = results['total']
    passed = results['passed']
    failed = results['failed']
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 70)
    print("🧪 VerusOS Detection Engine v2.0 - Test Results")
    print("=" * 70)
    
    print(f"\n📊 Overall Results:")
    print(f"   Total Tests: {total}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Pass Rate: {pass_rate:.1f}%")
    
    print(f"\n📋 Results by Category:")
    for category in ['CRISIS', 'GROOMING', 'VIOLENCE', 'SAFE']:
        cat_results = results['by_category'][category]
        total_cat = cat_results['total']
        passed_cat = cat_results['passed']
        failed_cat = cat_results['failed']
        
        if total_cat > 0:
            cat_pass_rate = (passed_cat / total_cat * 100)
            status = "✅" if cat_pass_rate == 100 else "⚠️" if cat_pass_rate >= 80 else "❌"
            print(f"   {status} {category:12} | Total: {total_cat:2} | Passed: {passed_cat:2} | Failed: {failed_cat:2} | Rate: {cat_pass_rate:5.1f}%")
    
    # Show failures if any
    if results['failures']:
        print(f"\n⚠️  Failed Tests ({len(results['failures'])}):")
        for i, failure in enumerate(results['failures'][:10], 1):  # Show first 10
            print(f"\n   {i}. Expected: {failure['expected']} → Got: {failure['detected']}")
            print(f"      Message: \"{failure['message'][:60]}...\"")
            print(f"      Score: {failure['score']}, Tier: {failure['tier']}")
        
        if len(results['failures']) > 10:
            print(f"\n   ... and {len(results['failures']) - 10} more failures")
    
    print("\n" + "=" * 70 + "\n")
    
    return pass_rate >= 80  # Return True if acceptable

def main():
    print("🔄 Loading test set...")
    test_cases = load_test_set()
    print(f"✅ Loaded {len(test_cases)} test cases")
    
    print("🚀 Running tests...")
    results = run_tests(test_cases)
    
    success = print_results(results)
    
    if success:
        print("✨ Detection Engine v2.0 VALIDATED ✨")
    else:
        print("⚠️  Detection Engine needs review")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
