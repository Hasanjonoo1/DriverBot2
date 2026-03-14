# bot/serializers.py
from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'c_chat_id', 'c_name', 'c_username', 'c_count',
            'c_phone', 'c_direction'
        ]
