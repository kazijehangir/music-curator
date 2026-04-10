def sanitize_pb_filter(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")
