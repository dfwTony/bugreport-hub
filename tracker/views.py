from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BugReportForm, RegisterForm, StaffUpdateForm
from .models import BugReport, StatusHistory
from .utils import find_possible_duplicate, notify

User = get_user_model()


def visible_reports(user):
    """Staff see every report; other users see only their own."""
    if user.is_staff:
        return BugReport.objects.all()
    return BugReport.objects.filter(reporter=user)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account has been created.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    reports = visible_reports(request.user)
    stats = {
        "total": reports.count(),
        "new": reports.filter(status="new").count(),
        "in_progress": reports.filter(status="in_progress").count(),
        "resolved": reports.filter(status__in=["resolved", "closed"]).count(),
    }
    return render(request, "tracker/dashboard.html", {"stats": stats, "recent": reports[:5]})


@login_required
def report_list(request):
    reports = visible_reports(request.user)
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    mine = request.GET.get("mine") == "1" and request.user.is_staff
    if q:
        reports = reports.filter(Q(title__icontains=q) | Q(module__icontains=q))
    if status:
        reports = reports.filter(status=status)
    if priority:
        reports = reports.filter(priority=priority)
    if mine:
        reports = reports.filter(assigned_to=request.user)
    context = {
        "reports": reports, "q": q, "status": status, "priority": priority, "mine": mine,
        "statuses": BugReport.STATUS_CHOICES, "priorities": BugReport.PRIORITY_CHOICES,
    }
    return render(request, "tracker/report_list.html", context)

@login_required
def report_create(request):
    form = BugReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.save()
        StatusHistory.objects.create(report=report, new_status=report.status,
                                     changed_by=request.user, note="Report submitted")

        staff = User.objects.filter(is_staff=True).exclude(pk=request.user.pk)
        notify([request.user], report, f"{report.ref} received: {report.title}")
        notify(staff, report, f"New report {report.ref}: {report.title}")

        duplicate = find_possible_duplicate(report.title, report.description, report.module,
                                            exclude_pk=report.pk)
        if duplicate:
            report.duplicate_of = duplicate
            report.save(update_fields=["duplicate_of"])
            notify(staff, report, f"{report.ref} may duplicate {duplicate.ref}; please review")
            messages.warning(request, f"Report {report.ref} submitted. It looks similar to "
                                      f"{duplicate.ref}, so staff will review it.")
        else:
            messages.success(request, f"Report {report.ref} submitted.")
        return redirect("report_detail", pk=report.pk)
    return render(request, "tracker/report_form.html", {"form": form})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(BugReport, pk=pk)
    if not request.user.is_staff and report.reporter_id != request.user.id:
        raise PermissionDenied

    update_form = None
    if request.user.is_staff:
        old_status = report.status          # read these before the form changes the report
        old_assignee = report.assigned_to_id
        update_form = StaffUpdateForm(request.POST or None, instance=report)
        if request.method == "POST" and update_form.is_valid():
            report = update_form.save()
            note = update_form.cleaned_data["note"]
            if report.status != old_status or note:
                StatusHistory.objects.create(
                    report=report, old_status=old_status, new_status=report.status,
                    changed_by=request.user, note=note,
                )
            if report.status != old_status:
                notify([report.reporter], report,
                       f"{report.ref} is now {report.get_status_display()}")
            if (report.assigned_to_id and report.assigned_to_id != old_assignee
                    and report.assigned_to_id != request.user.id):
                notify([report.assigned_to], report, f"{report.ref} was assigned to you")
            messages.success(request, "Report updated.")
            return redirect("report_detail", pk=report.pk)

    context = {"report": report, "history": report.history.all(), "update_form": update_form}
    return render(request, "tracker/report_detail.html", context)

@login_required
def notifications(request):
    if request.method == "POST":
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect("notifications")
    items = request.user.notifications.select_related("report")[:50]
    return render(request, "tracker/notifications.html", {"items": items})


@login_required
def summary(request):
    if not request.user.is_staff:
        raise PermissionDenied
    reports = BugReport.objects.all()
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    if date_from:
        reports = reports.filter(created_at__date__gte=date_from)
    if date_to:
        reports = reports.filter(created_at__date__lte=date_to)

    def tally(field, labels=None):
        rows = reports.values(field).annotate(n=Count("id")).order_by("-n")
        return [((labels or {}).get(r[field], r[field]) or "Uncategorized", r["n"]) for r in rows]

    context = {
        "total": reports.count(), "date_from": date_from, "date_to": date_to,
        "by_status": tally("status", dict(BugReport.STATUS_CHOICES)),
        "by_priority": tally("priority", dict(BugReport.PRIORITY_CHOICES)),
        "by_category": tally("category__name"),
    }
    return render(request, "tracker/summary.html", context)