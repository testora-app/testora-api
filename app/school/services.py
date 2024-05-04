import uuid

def create_school_code(short_name):
    return f"{short_name}-{uuid.uuid4()[:6]}"