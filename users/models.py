from django.db import models
from django.contrib.auth.models import User

class Carteira(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Carteira de {self.usuario.username}'

class Transferencia(models.Model):
    origem = models.ForeignKey(Carteira, related_name='transferencias_origem', on_delete=models.CASCADE)
    destino = models.ForeignKey(Carteira, related_name='transferencias_destino', on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transferência de {self.valor} de {self.origem.usuario.username} para {self.destino.usuario.username}'
