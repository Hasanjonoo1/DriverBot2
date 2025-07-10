from django.urls import path

from bot.views.api.views import OrderCreateAPIView
from bot.views.webhook.get_webhook import handle_updates

urlpatterns = [
    path("webhook/<str:bot_id>/updates", handle_updates),
    path('orders/create/', OrderCreateAPIView.as_view(), name='order-create'),
]