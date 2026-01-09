def validate_non_empty(value: str, field_name: str):
    """Raise ValueError if string is empty"""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return value

def validate_positive_int(value: int, field_name: str):
    """Raise ValueError if integer is not positive"""
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value
