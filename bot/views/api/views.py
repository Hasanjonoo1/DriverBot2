# bot/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from bot.models import Order
from bot.serializers import OrderSerializer

class OrderCreateAPIView(APIView):
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response({"message": "Order created", "id": order.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
