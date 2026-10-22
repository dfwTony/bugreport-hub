from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BugReport(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    title = models.CharField(max_length=200)
    module = models.CharField(max_length=100)
    description = models.TextField()
    steps_to_reproduce = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="new")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="reports")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="assigned_reports")
    duplicate_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="possible_duplicates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def ref(self):
        return f"BR-{self.pk:04d}"

    def __str__(self):
        return f"{self.ref} {self.title}"

    @property
    def status_badge(self):
        return {"new": "primary", "in_progress": "warning text-dark",
                "resolved": "success", "closed": "secondary"}[self.status]

    @property
    def priority_badge(self):
        return {"low": "secondary", "medium": "info text-dark",
                "high": "warning text-dark", "critical": "danger"}[self.priority]

class StatusHistory(models.Model):
    report = models.ForeignKey(BugReport, on_delete=models.CASCADE, related_name="history")
    old_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name_plural = "status history"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="notifications")
    report = models.ForeignKey(BugReport, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]