from os import environ

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

User = get_user_model()  # noqa: N806


def create_admin_user():
    username = environ.get("ADMIN_NAME", "super_secret_admin_name")
    logger.debug(f"Start create super user with username: `{username}`")
    password = environ.get("ADMIN_PASSWORD", "super_secret_admin_password")

    if User.objects.filter(username=username).exists():
        logger.debug(f"Super user with username: `{username}` already exists!")
        return

    user = User.objects.create_user(username=username, password=password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    logger.debug(f"Super user with username: `{username}` created!")


class Command(BaseCommand):
    help = "Создание администратора"

    def handle(self, *args, **options):
        logger.debug("COMMAND create_admin_user")
        try:
            create_admin_user()
        except Exception:
            logger.exception("Unable to create super user!")
