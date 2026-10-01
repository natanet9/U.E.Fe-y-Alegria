from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Gestion escolar'

    def ready(self):
        from .tracing import install_database_connection_tracing

        install_database_connection_tracing()
