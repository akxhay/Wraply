def serialize_model(obj):
    """Convert SQLAlchemy model to dictionary safely"""
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


def serialize_list(objects):
    return [serialize_model(obj) for obj in objects]