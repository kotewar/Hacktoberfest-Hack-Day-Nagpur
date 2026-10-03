from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from src.database import get_topic_mastery_record, save_or_update_topic_mastery

def calculate_sm2(
    quality: int,
    repetitions: int = 0,
    interval_days: int = 1,
    ease_factor: float = 2.5,
    base_date: datetime = None
) -> Tuple[int, int, float, datetime]:
    """
    Computes new repetitions, interval_days, ease_factor, and next_review date
    based on the SuperMemo-2 (SM-2) spaced repetition algorithm.

    Parameters:
    - quality: Integer in range [0, 5] (0 = blackout, 5 = perfect recall)
    - repetitions: Number of consecutive successful recalls (quality >= 3)
    - interval_days: Current review interval in days
    - ease_factor: Current ease factor (minimum 1.3)
    - base_date: Date from which next_review is calculated (default: now)

    Returns:
    - (new_repetitions, new_interval_days, new_ease_factor, next_review_datetime)
    """
    quality = max(0, min(5, int(quality)))
    if base_date is None:
        base_date = datetime.now()

    # Calculate new ease factor: EF' = max(1.3, EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
    new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease_factor = max(1.3, round(new_ease_factor, 3))

    if quality < 3:
        # Failure: restart repetitions
        new_repetitions = 0
        new_interval_days = 1
    else:
        # Success: increment repetitions and compute next interval
        if repetitions == 0:
            new_interval_days = 1
        elif repetitions == 1:
            new_interval_days = 6
        else:
            new_interval_days = max(1, round(interval_days * new_ease_factor))
        new_repetitions = repetitions + 1

    next_review = base_date + timedelta(days=new_interval_days)
    return new_repetitions, new_interval_days, new_ease_factor, next_review


def score_to_quality(score: float, total: int) -> int:
    """
    Maps quiz performance (0.0 to 1.0) to an SM-2 quality grade from 0 to 5.
    """
    if total <= 0:
        return 0
    ratio = max(0.0, min(1.0, score / total))
    if ratio >= 0.95:
        return 5
    elif ratio >= 0.80:
        return 4
    elif ratio >= 0.65:
        return 3
    elif ratio >= 0.50:
        return 2
    elif ratio >= 0.30:
        return 1
    else:
        return 0


def update_topic_after_quiz(
    user_id: int,
    topic_name: str,
    score: float,
    total: int
) -> Dict[str, Any]:
    """
    Updates a user's topic mastery and SM-2 spaced repetition state after a quiz.
    """
    topic_name = topic_name.strip() or "General Knowledge"
    current_record = get_topic_mastery_record(user_id, topic_name)
    
    if current_record:
        prev_attempts = current_record["attempts"]
        prev_mastery = current_record["mastery_percentage"]
        repetitions = current_record["repetitions"]
        interval_days = current_record["interval_days"]
        ease_factor = current_record["ease_factor"]
    else:
        prev_attempts = 0
        prev_mastery = 0.0
        repetitions = 0
        interval_days = 1
        ease_factor = 2.5

    quality = score_to_quality(score, total)
    quiz_percent = (score / total * 100) if total > 0 else 0.0

    # Moving average for mastery percentage with a learning bias
    if prev_attempts == 0:
        new_mastery = round(quiz_percent, 1)
    else:
        # 40% current quiz, 60% historical mastery
        new_mastery = round((prev_mastery * 0.6) + (quiz_percent * 0.4), 1)
    new_mastery = max(0.0, min(100.0, new_mastery))

    new_rep, new_interval, new_ef, next_rev = calculate_sm2(
        quality=quality,
        repetitions=repetitions,
        interval_days=interval_days,
        ease_factor=ease_factor
    )

    save_or_update_topic_mastery(
        user_id=user_id,
        topic_name=topic_name,
        mastery_percentage=new_mastery,
        repetitions=new_rep,
        interval_days=new_interval,
        ease_factor=new_ef,
        next_review=next_rev
    )

    return {
        "topic_name": topic_name,
        "quality": quality,
        "mastery_percentage": new_mastery,
        "repetitions": new_rep,
        "interval_days": new_interval,
        "ease_factor": new_ef,
        "next_review": next_rev
    }
