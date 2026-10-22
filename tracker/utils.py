from difflib import SequenceMatcher

from .models import BugReport, Notification


def _clean(text):
    return " ".join(text.lower().split())


def _similarity(a, b):
    return SequenceMatcher(None, _clean(a), _clean(b)).ratio()


def find_possible_duplicate(title, description, module, exclude_pk=None, threshold=0.6):
    """Return the most similar open report in the same module, or None.

    Score = 60% title similarity + 40% description similarity (0 to 1).
    """
    candidates = (BugReport.objects.filter(module__iexact=module)
                  .exclude(status="closed").order_by("-created_at")[:200])
    best, best_score = None, 0.0
    for report in candidates:
        if report.pk == exclude_pk:
            continue
        score = (0.6 * _similarity(title, report.title)
                 + 0.4 * _similarity(description, report.description))
        if score > best_score:
            best, best_score = report, score
    return best if best_score >= threshold else None


def notify(users, report, message):
    Notification.objects.bulk_create(
        [Notification(user=u, report=report, message=message[:255]) for u in set(users)]
    )