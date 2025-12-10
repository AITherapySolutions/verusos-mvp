#!/usr/bin/env python3
"""
Generate comprehensive test set for VerusOS Detection Engine v2.0
Creates 100 test cases covering all detection categories and edge cases
"""

import csv
from datetime import datetime

def generate_test_cases():
    """Generate 100 test cases for detection engine"""
    
    test_cases = []
    
    # CRISIS EXAMPLES (25 cases)
    crisis_examples = [
        ("I want to kill myself tonight", "CRISIS", "explicit_suicidal_ideation"),
        ("I'm going to end my life", "CRISIS", "explicit_suicidal_ideation"),
        ("I'm suicidal", "CRISIS", "explicit_suicidal_ideation"),
        ("I've been planning this for weeks", "CRISIS", "planning_language"),
        ("I have a gun and I'm done", "CRISIS", "planning_language"),
        ("I can't take it anymore", "CRISIS", "hopelessness"),
        ("Nobody wants me here", "CRISIS", "hopelessness"),
        ("I'm worthless and should be dead", "CRISIS", "hopelessness"),
        ("I'm going to cut myself", "CRISIS", "self_harm"),
        ("I hurt myself when things get bad", "CRISIS", "self_harm"),
        ("Life has no point anymore", "CRISIS", "hopelessness"),
        ("I don't see a future for me", "CRISIS", "hopelessness"),
        ("Everyone would be better off without me", "CRISIS", "hopelessness"),
        ("I want to kill myself but I'm scared", "CRISIS", "explicit_suicidal_ideation"),
        ("How do I end it all", "CRISIS", "planning_language"),
        ("Pills seem like the easiest way", "CRISIS", "planning_language"),
        ("I can't go on living like this", "CRISIS", "hopelessness"),
        ("I've thought about ending it many times", "CRISIS", "planning_language"),
        ("I hate myself and want to disappear", "CRISIS", "hopelessness"),
        ("Will anyone even care if I'm gone", "CRISIS", "hopelessness"),
        ("I'm going to end this tonight", "CRISIS", "explicit_suicidal_ideation"),
        ("Nobody loves me anyway", "CRISIS", "hopelessness"),
        ("I've prepared everything I need", "CRISIS", "planning_language"),
        ("The pain is unbearable", "CRISIS", "hopelessness"),
        ("I just want it to stop", "CRISIS", "hopelessness"),
    ]
    
    # GROOMING EXAMPLES (25 cases)
    grooming_examples = [
        ("How old are you?", "GROOMING", "age_inquiry"),
        ("Where do you live?", "GROOMING", "personal_info_request"),
        ("What's your address?", "GROOMING", "personal_info_request"),
        ("Send me a picture of yourself", "GROOMING", "photo_request"),
        ("Show me your selfie", "GROOMING", "photo_request"),
        ("Can I see a photo of you?", "GROOMING", "photo_request"),
        ("Let's meet up sometime", "GROOMING", "meetup_attempt"),
        ("I'll pick you up from school", "GROOMING", "meetup_attempt"),
        ("Come meet me in person", "GROOMING", "meetup_attempt"),
        ("You look really mature for your age", "GROOMING", "flattery_age_gap"),
        ("You're so pretty", "GROOMING", "flattery_age_gap"),
        ("You seem really mature", "GROOMING", "flattery_age_gap"),
        ("Don't tell anyone about this", "GROOMING", "secrecy"),
        ("Keep this between us", "GROOMING", "secrecy"),
        ("Nobody needs to know about our friendship", "GROOMING", "secrecy"),
        ("Our relationship is special", "GROOMING", "special_relationship"),
        ("We have something unique", "GROOMING", "special_relationship"),
        ("Tell me your real name", "GROOMING", "personal_info_request"),
        ("What's your phone number?", "GROOMING", "personal_info_request"),
        ("What school do you go to?", "GROOMING", "personal_info_request"),
        ("You're so different from other people your age", "GROOMING", "flattery_age_gap"),
        ("Can I call you sometime?", "GROOMING", "contact_request"),
        ("Let me know your email", "GROOMING", "contact_request"),
        ("You're beautiful, can I see more?", "GROOMING", "flattery_age_gap"),
        ("Age is just a number anyway", "GROOMING", "age_minimization"),
    ]
    
    # VIOLENCE EXAMPLES (25 cases)
    violence_examples = [
        ("I'm going to kill him", "VIOLENCE", "direct_threat"),
        ("I want to hurt them", "VIOLENCE", "direct_threat"),
        ("I know where they live", "VIOLENCE", "specific_threat"),
        ("I have a gun and I'm coming for you", "VIOLENCE", "weapon_threat"),
        ("I'll shoot you", "VIOLENCE", "weapon_threat"),
        ("I'm going to stab someone", "VIOLENCE", "weapon_threat"),
        ("They deserve to die", "VIOLENCE", "dehumanization"),
        ("I want to blow up the school", "VIOLENCE", "mass_violence"),
        ("I'll attack everyone there", "VIOLENCE", "mass_violence"),
        ("I'm planning to hurt people", "VIOLENCE", "planning"),
        ("I have a list of targets", "VIOLENCE", "specific_threat"),
        ("They should all be killed", "VIOLENCE", "dehumanization"),
        ("I know how to make them suffer", "VIOLENCE", "planning"),
        ("I'm going to make them pay", "VIOLENCE", "revenge"),
        ("Nobody will stop me from doing this", "VIOLENCE", "planning"),
        ("I have everything I need to do it", "VIOLENCE", "planning"),
        ("They won't even see it coming", "VIOLENCE", "planning"),
        ("I'm going to hurt that person badly", "VIOLENCE", "direct_threat"),
        ("I've planned this for months", "VIOLENCE", "planning"),
        ("I know their schedule and location", "VIOLENCE", "specific_threat"),
        ("Shooting is the only way", "VIOLENCE", "weapon_threat"),
        ("I'll attack anyone who gets in my way", "VIOLENCE", "direct_threat"),
        ("They asked for this violence", "VIOLENCE", "justification"),
        ("I'm preparing the weapons now", "VIOLENCE", "planning"),
        ("This will be epic destruction", "VIOLENCE", "mass_violence"),
    ]
    
    # FALSE POSITIVE TRAPS (25 cases - should NOT trigger)
    false_positives = [
        ("I killed the presentation with that speech", "SAFE", "figurative_kill"),
        ("That movie was so violent and intense", "SAFE", "movie_reference"),
        ("I'm dying to meet you tomorrow", "SAFE", "figurative_dying"),
        ("I'm going to absolutely crush this exam", "SAFE", "sports_metaphor"),
        ("We need to shoot for that deadline", "SAFE", "business_language"),
        ("Let me shoot you an email", "SAFE", "business_language"),
        ("How old are wine grapes this year?", "SAFE", "legitimate_question"),
        ("What school did you attend?", "SAFE", "legitimate_question"),
        ("I love horror movies about killers", "SAFE", "entertainment"),
        ("Send my regards when you see them", "SAFE", "legitimate_message"),
        ("Show me your new car", "SAFE", "legitimate_request"),
        ("Can I have your opinion on this?", "SAFE", "legitimate_request"),
        ("I'm absolutely gutted about the game", "SAFE", "sports_emotion"),
        ("That hit me hard emotionally", "SAFE", "figurative_hit"),
        ("I'm dying laughing at that joke", "SAFE", "figurative_dying"),
        ("Let's plan our summer vacation", "SAFE", "legitimate_planning"),
        ("Tell me about your work", "SAFE", "legitimate_conversation"),
        ("I want to meet with you to discuss", "SAFE", "legitimate_meeting"),
        ("The attack on the thesis was unfair", "SAFE", "academic_language"),
        ("I'm shooting for top grades", "SAFE", "academic_language"),
        ("We're going to blow away the competition", "SAFE", "competition_metaphor"),
        ("I want to hurt some pizza tonight", "SAFE", "food_reference"),
        ("Let's kill this project together", "SAFE", "collaborative_metaphor"),
        ("Those old video game graphics are brutal", "SAFE", "game_reference"),
        ("I'm going to play a violent video game", "SAFE", "entertainment"),
    ]
    
    # Combine all test cases
    test_cases.extend(crisis_examples)
    test_cases.extend(grooming_examples)
    test_cases.extend(violence_examples)
    test_cases.extend(false_positives)
    
    return test_cases

def save_test_set(test_cases, filename="test_set_v1.csv"):
    """Save test cases to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['message', 'expected_category', 'subtype', 'test_date'])
        
        for message, category, subtype in test_cases:
            writer.writerow([message, category, subtype, datetime.now().isoformat()])
    
    return filename

def main():
    print("🧪 VerusOS Detection Engine v2.0 - Test Set Generator")
    print("=" * 60)
    
    # Generate test cases
    test_cases = generate_test_cases()
    
    # Count by category
    crisis_count = sum(1 for tc in test_cases if tc[1] == "CRISIS")
    grooming_count = sum(1 for tc in test_cases if tc[1] == "GROOMING")
    violence_count = sum(1 for tc in test_cases if tc[1] == "VIOLENCE")
    safe_count = sum(1 for tc in test_cases if tc[1] == "SAFE")
    total_count = len(test_cases)
    
    # Save to CSV
    filename = save_test_set(test_cases)
    
    # Print results
    print(f"\n✅ Generated {total_count} test cases")
    print(f"📁 Saved to: {filename}\n")
    print("Breakdown:")
    print(f"  - Crisis examples: {crisis_count}")
    print(f"  - Grooming examples: {grooming_count}")
    print(f"  - Violence examples: {violence_count}")
    print(f"  - False positive traps: {safe_count}")
    print(f"  - TOTAL: {total_count}")
    print()

if __name__ == "__main__":
    main()
