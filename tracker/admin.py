from django.contrib import admin

from .models import BugReport, Category, Notification, StatusHistory

admin.site.register(Category)
admin.site.register(BugReport)
admin.site.register(StatusHistory)
admin.site.register(Notification)
