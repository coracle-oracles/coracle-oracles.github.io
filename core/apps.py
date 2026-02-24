from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from django.conf import settings

        # Only auto-start reconciliation in production (database backend)
        if settings.DEBUG:
            return

        # Import here to avoid AppRegistryNotReady
        from django_tasks_db.models import DBTaskResult
        from .tasks import reconcile_pending_orders

        # Check if reconciliation is already scheduled or running
        task_path = 'core.tasks.reconcile_pending_orders'
        pending_exists = DBTaskResult.objects.filter(
            task_path=task_path,
            status__in=['NEW', 'RUNNING'],
        ).exists()

        if not pending_exists:
            reconcile_pending_orders.enqueue()
