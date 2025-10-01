from django.db import models
from django.utils import timezone
from datetime import timedelta

class ForoQuerySet(models.QuerySet):
    def recientes(self, dias=7):
        return self.filter(fecha_creacion__gte=timezone.now() - timedelta(days=dias))

    def populares(self, min_likes=10):
        return self.annotate(num_likes=models.Count("likes")).filter(num_likes__gte=min_likes)

    def por_etiqueta(self, etiqueta_nombre):
        return self.filter(etiquetas__nombre__iexact=etiqueta_nombre)
