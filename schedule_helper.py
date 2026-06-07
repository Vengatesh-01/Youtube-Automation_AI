import datetime

def get_next_publish_time(hour=10, minute=0, tz_offset_hours=5.5):
    """Return an RFC3339 timestamp for the next occurrence of the given hour (default 10:00).
    tz_offset_hours is the offset from UTC (e.g., 5.5 for IST)."""
    now_utc = datetime.datetime.utcnow()
    # apply offset to get local time
    now_local = now_utc + datetime.timedelta(hours=tz_offset_hours)
    target = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now_local >= target:
        # schedule for next day
        target += datetime.timedelta(days=1)
    # convert back to UTC string
    target_utc = target - datetime.timedelta(hours=tz_offset_hours)
    return target_utc.isoformat() + "Z"
