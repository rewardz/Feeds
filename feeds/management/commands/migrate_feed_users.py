from __future__ import print_function
from feeds.models import Post, PostCertificateRecord
from django.core.management.base import BaseCommand
from rewardz_utils.processmonitor.decorators import write_process_monitor_logs


class Command(BaseCommand):
    help = """Used to migrate Post[user] to Post[users] model"""

    @write_process_monitor_logs(site="skor", command="migrate_feed_users")
    def handle(self, *args, **options):
        posts = Post.objects.all()
        cnt = posts.count()
        print(cnt)
        for post in posts.iterator():
            try:
                cnt -= 1
                print(cnt)
                user = post.user
                if user is not None and not post.users.all():
                    post.users.add(user)
                    if post.users.all().first() != user:
                        raise Exception("Invalid user migration {}".format(post.id))
            except Exception as e:
                print("Exception {}".format(str(e)))
                continue

        appreciation_cert_records = PostCertificateRecord.objects.all()
        for appreciation_cert_record in appreciation_cert_records:
            if appreciation_cert_record.user:
                continue
            appreciation_cert_record.user = appreciation_cert_record.post.user
            appreciation_cert_record.save()
