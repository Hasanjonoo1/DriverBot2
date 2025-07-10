from django.contrib import admin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin, TabularInline

from .models import BotUser, PrivateGroup, Order, OrderHistory

admin.site.unregister(Group)

class OrderHistoryInlineTabular(TabularInline):
    model = OrderHistory
    list_display = ('id', 'order', 'doer', 'status', 'created_at')

    readonly_fields = ('id', 'order', 'doer', 'status', 'created_at')
    ordering = ('-created_at',)
    extra = 0

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        'id', 'c_name', 'c_phone', 'c_direction',
        'c_count', 'status', 'd_name',
        'created_at', 'updated_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('c_name', 'c_phone', 'c_direction', 'd_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    inlines = (OrderHistoryInlineTabular,)

    fieldsets = (
        ("📌 Mijoz haqida", {
            'fields': (
                'c_chat_id', 'c_name', 'c_username', 'c_phone', 'c_count', 'c_direction'
            )
        }),
        ("🚖 Haydovchi haqida", {
            'fields': (
                'd_id', 'd_name', 'd_phone'
            )
        }),
        ("📍 Buyurtma holati", {
            'fields': (
                'status', 'group_chat_id', 'group_message_id'
            )
        }),
        ("🕒 Vaqt ma'lumotlari", {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(OrderHistory)
class OrderHistoryAdmin(ModelAdmin):
    list_display = ('id', 'order', 'doer', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__c_name', 'doer')
    ordering = ('-created_at',)
    autocomplete_fields = ['order']
    readonly_fields = ('created_at',)


@admin.register(BotUser)
class BotUserAdmin(ModelAdmin):
    list_display = ("full_name", "phone", "cash", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone", "chat_id")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(PrivateGroup)
class PrivateGroupAdmin(ModelAdmin):
    list_display = ("title", "chat_id")
    search_fields = ("title", "chat_id")

