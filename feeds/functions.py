from __future__ import division, print_function, unicode_literals

from feeds.constants import POST_TYPE
from feeds.models import Post
from feeds.serializers import DocumentsSerializer, ImagesSerializer

def create_feedback_post(user, title, description, **kwargs):
    """
    Params:
    user (CustomUser): the user who creates a feedback
    title (String): the title of the feedback post (not null)
    description (String): the description to provide details (not null)
    kwargs:
      - images: Images attached
      - documents: Documents attached

    Return: 
      - True if post created successfully
      - False if exception Raised
    """
    try:
        post = Post.objects.create(
            created_by=user, organization=user.organization, title=title,
            description=description, post_type=POST_TYPE.FEEDBACK_POST
        )
        images = kwargs.get("images", None)
        documents = kwargs.get("documents", None)
        if images:
            for img in images:
                data = {"post": post.pk}
                data['image'] = img
                image_serializer = ImagesSerializer(data=data)
                if image_serializer.is_valid():
                    image_serializer.save()
                else:
                    return False

        if documents:
            for doc in documents:
                data = {'post': post.pk}
                data['document'] = doc
                document_serializer = DocumentsSerializer(data=data)
                if document_serializer.is_valid():
                    document_serializer.save()
                else:
                    return False
        return True
    except Exception:
        return False

