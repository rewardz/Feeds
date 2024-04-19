from __future__ import print_function
from feeds.models import Post
from django.core.management.base import BaseCommand
from rewardz_utils.processmonitor.decorators import write_process_monitor_logs


class Command(BaseCommand):
    help = """Used to migrate Post[user] to Post[users] model"""

    @write_process_monitor_logs(site="skor", command="migrate_feed_users")
    def handle(self, *args, **options):
        posts = Post.objects.all()
        for post in posts.iterator():
            try:
                user = post.user
                if user is not None and not post.users.all():
                    post.users.add(user)
                    if post.users.all().first() != user:
                        raise Exception("Invalid user migration {}".format(post.id))
            except Exception as e:
                print("Exception {}".format(str(e)))
                continue
