from __future__ import division, print_function, unicode_literals

from feeds.constants import POST_TYPE
from feeds.models import Post

def create_feedback_post(user, title, description):
    try:
        Post.objects.create(
            created_by=user, organization=user.organization, title=title,
            description=description, post_type=POST_TYPE.FEEDBACK_POST
        )
        return True
    except Exception:
        return False

