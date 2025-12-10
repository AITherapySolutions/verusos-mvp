from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import Detection


class TemporalTrackingService:
    
    def check_temporal_patterns(
        self,
        db: Session,
        user_id_hash: str
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        
        time_72h = now - timedelta(hours=72)
        alerts_72h = db.query(Detection).filter(
            Detection.user_id_hash == user_id_hash,
            Detection.timestamp > time_72h,
            Detection.risk_tier <= 2
        ).order_by(Detection.timestamp).all()
        
        time_14d = now - timedelta(days=14)
        alerts_14d_count = db.query(func.count(Detection.id)).filter(
            Detection.user_id_hash == user_id_hash,
            Detection.timestamp > time_14d
        ).scalar() or 0
        
        if len(alerts_72h) >= 2:
            pattern = 'repeat_alerts_72h'
            concern_level = 'elevated'
            trajectory = self._calculate_trajectory(alerts_72h)
        elif alerts_14d_count >= 3:
            pattern = 'multiple_alerts_14d'
            concern_level = 'monitoring'
            trajectory = 'monitoring'
        else:
            pattern = 'isolated_event'
            concern_level = 'baseline'
            trajectory = 'stable'
        
        return {
            'alerts_72h': len(alerts_72h),
            'alerts_14d': alerts_14d_count,
            'pattern': pattern,
            'concern_level': concern_level,
            'trajectory': trajectory,
            'note': f"{len(alerts_72h)} alerts in last 72 hours, {alerts_14d_count} in last 14 days"
        }
    
    def _calculate_trajectory(self, alerts: list) -> str:
        if len(alerts) < 2:
            return 'insufficient_data'
        
        scores = [alert.risk_score for alert in alerts]
        
        if len(scores) >= 2:
            first_half_avg = sum(scores[:len(scores)//2]) / max(len(scores)//2, 1)
            second_half_avg = sum(scores[len(scores)//2:]) / max(len(scores) - len(scores)//2, 1)
            
            if second_half_avg > first_half_avg * 1.1:
                return 'escalating'
            elif second_half_avg < first_half_avg * 0.9:
                return 'de-escalating'
            else:
                return 'stable'
        
        return 'stable'
    
    def get_previous_alerts_count(
        self,
        db: Session,
        user_id_hash: str,
        days: int = 14
    ) -> int:
        time_window = datetime.utcnow() - timedelta(days=days)
        count = db.query(func.count(Detection.id)).filter(
            Detection.user_id_hash == user_id_hash,
            Detection.timestamp > time_window
        ).scalar() or 0
        return count


temporal_tracker = TemporalTrackingService()
