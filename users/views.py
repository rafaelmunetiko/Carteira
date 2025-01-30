from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import Carteira
from django.db import transaction
from rest_framework import status
from django.utils.dateparse import parse_date

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_transfers(request):
    user = request.user
    carteira = Carteira.objects.get(usuario=user)
    inicio = request.query_params.get("inicio")
    fim = request.query_params.get("fim")

    transferencias = Transferencia.objects.filter(origem=carteira)

    if inicio:
        transferencias = transferencias.filter(data__gte=parse_date(inicio))
    if fim:
        transferencias = transferencias.filter(data__lte=parse_date(fim))

    response_data = [
        {
            "destino": transferencia.destino.usuario.username,
            "valor": transferencia.valor,
            "data": transferencia.data
        }
        for transferencia in transferencias
    ]

    return Response(response_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_funds(request):
    user = request.user
    destinatario_username = request.data.get("destinatario")
    valor = request.data.get("valor")

    if not destinatario_username or not valor:
        return Response({"error": "Destinatário e valor são obrigatórios."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        valor = float(valor)
        if valor <= 0:
            return Response({"error": "O valor deve ser maior que zero."}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"error": "Valor inválido."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        carteira_origem = Carteira.objects.get(usuario=user)
        carteira_destino = Carteira.objects.get(usuario__username=destinatario_username)
    except Carteira.DoesNotExist:
        return Response({"error": "Carteira de origem ou destino não encontrada."}, status=404)

    if carteira_origem.saldo < valor:
        return Response({"error": "Saldo insuficiente."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            carteira_origem.saldo -= valor
            carteira_destino.saldo += valor
            carteira_origem.save()
            carteira_destino.save()

            # Registrar a transferência
            Transferencia.objects.create(
                origem=carteira_origem,
                destino=carteira_destino,
                valor=valor
            )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"mensagem": f"Transferência de {valor} para {destinatario_username} concluída."})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_balance(request):
    user = request.user
    valor = request.data.get("valor")

    if not valor or float(valor) <= 0:
        return Response({"error": "Valor inválido."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            carteira, _ = Carteira.objects.get_or_create(usuario=user)
            carteira.saldo += float(valor)
            carteira.save()
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"mensagem": f"Adicionado {valor} ao saldo. Novo saldo: {carteira.saldo}"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_balance(request):
    user = request.user
    try:
        carteira = Carteira.objects.get(usuario=user)
    except Carteira.DoesNotExist:
        return Response({"error": "Carteira não encontrada."}, status=404)
    
    return Response({"saldo": carteira.saldo})

# Criar Usuário
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def criar_usuario(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        user = User.objects.create_user(username=username, password=password)
        return Response({"msg": "Usuário criado com sucesso!"}, status=status.HTTP_201_CREATED)

# Login (Gerar Token JWT)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = User.objects.filter(username=username).first()
    
    if user and user.check_password(password):
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response({"msg": "Credenciais inválidas!"}, status=status.HTTP_400_BAD_REQUEST)
