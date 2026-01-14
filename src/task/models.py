from django.db import models
from common.models import Category
from domain.enums.status_type import StatusType
from user.models import User


status_types = [(type.value, type.value) for type in StatusType]


class Status(models.Model):
    name = models.CharField(max_length=31)
    type = models.CharField(choices=status_types, default=status_types[0][0])
    color = models.CharField(max_length=9)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "status"


class Sprint(models.Model):
    name = models.CharField(max_length=63)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "sprint"


class Tag(models.Model):
    name = models.CharField(max_length=63)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tag"


class Subtask(models.Model):
    name = models.CharField(max_length=127)
    completed = models.BooleanField(default=False)
    task = models.ForeignKey(to='Task', on_delete=models.CASCADE, related_name='subtasks')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "subtask"


class Task(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, default=None)
    finished_at = models.DateTimeField(null=True, default=None)
    status = models.ForeignKey(to=Status, on_delete=models.SET_NULL, null=True)
    sprint = models.ForeignKey(to=Sprint, on_delete=models.SET_NULL, null=True, default=None)
    tags = models.ManyToManyField(to=Tag)
    category = models.ForeignKey(to=Category, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "task"
        ordering = ["-created_at"]