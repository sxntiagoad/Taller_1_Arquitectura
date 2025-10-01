from django.db import models
from .querysets import ForoQuerySet

class ForoManager(models.Manager):
    def get_queryset(self):
        return ForoQuerySet(self.model, using=self._db)

    # Métodos accesibles desde objects
    def recientes(self, dias=7):
        return self.get_queryset().recientes(dias)

    def populares(self, min_likes=10):
        return self.get_queryset().populares(min_likes)

    def por_etiqueta(self, etiqueta_nombre):
        return self.get_queryset().por_etiqueta(etiqueta_nombre)
