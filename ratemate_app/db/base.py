from sqlalchemy.orm import declarative_base

Base = declarative_base()

def import_models():
    from ratemate_app.models.user import User
    from ratemate_app.models.post import Post
    from ratemate_app.models.comment import Comment
    from ratemate_app.models.rating import Rating
    from ratemate_app.models.follow import Follow
    from ratemate_app.models.chat import Chat
    from ratemate_app.models.message import Message
    from ratemate_app.models.media import Media
    from ratemate_app.models.lowkey import Lowkey, LowkeyView