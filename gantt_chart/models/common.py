from django.contrib.admin.options import get_content_type_for_model
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


class UniversalCommentManager(models.Manager):
    def filter_with_content_type(self, content_type: type[models.Model], *args, **kwargs):
        _content_type = get_content_type_for_model(content_type)
        return super().filter(content_type=_content_type, *args, **kwargs)


class UniversalComment(models.Model):
    """Комментарий"""

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="content_universal_comment",
        verbose_name="content type",
    )
    object_id = models.CharField("Индентификатор объекта", max_length=64, blank=False, null=False)
    comment = models.TextField("Комментарий", db_index=True, blank=False, null=False)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="author_universal_comment",
        verbose_name="Автор комментария",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True, blank=False, null=False)

    objects = UniversalCommentManager()

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self) -> str:
        return f"{self.author} |{self.created_at}|: {self.comment}"
