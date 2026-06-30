import datetime

def format_timestamp(value: str) -> str:
    """
    Formats an ISO-8601 timestamp string into DD-MM-YYYY HH:MM:SS format.
    If parsing fails, returns the original value.
    """
    if not value:
        return value
        
    try:
        # Handle 'Z' suffix since fromisoformat in older Pythons might not like it
        clean_value = value.replace('Z', '+00:00')
        dt = datetime.datetime.fromisoformat(clean_value)
        return dt.strftime("%d-%m-%Y %H:%M:%S")
    except Exception:
        return value
