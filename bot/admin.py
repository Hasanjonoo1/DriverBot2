from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Sum
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Driver, PrivateGroup, Order, OrderHistory, TicketDetail, Ticket

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


@admin.register(Driver)
class DriverAdmin(ModelAdmin):
    list_display = (
        "full_name",
        "phone",
        "cash",
        "limit_target_per_24hours",
        "limit_count_per_target",
        "is_active",
        "blocked_info",
        "created_at"
    )
    list_filter = ("status", "is_blocked", "created_at")
    search_fields = ("full_name", "phone", "chat_id")
    readonly_fields = ("created_at", ) #"blocked_until", "is_blocked")
    ordering = ("-created_at",)

    fieldsets = (
        ("👤 Asosiy maʼlumotlar", {
            "fields": ("full_name", "phone", "chat_id", "status")
        }),
        ("📈 Limitlar", {
            "fields": ("limit_target_per_24hours", "limit_count_per_target"),
        }),
        ("💳 Moliyaviy va texnik", {
            "fields": ("cash", "is_blocked", "blocked_until", "created_at"),
        }),
    )

    def is_active(self, obj):
        return "✅" if obj.status else "⛔️"
    is_active.short_description = "Holat"

    def blocked_info(self, obj):
        if obj.is_blocked:
            if obj.blocked_until:
                return format_html(
                    "<span style='color: red;'>Bloklangan ({})</span>",
                    obj.blocked_until.strftime('%d.%m.%Y %H:%M')
                )
            return format_html("<span style='color: red;'>Bloklangan</span>")
        return format_html("<span style='color: green;'>Bloklanmagan</span>")
    blocked_info.short_description = "Blok holati"




@admin.register(PrivateGroup)
class PrivateGroupAdmin(ModelAdmin):
    list_display = ("title", "chat_id")
    search_fields = ("title", "chat_id")


# TabularInline orqali TicketDetail ni biriktirish
class TicketDetailInline(TabularInline):
    model = TicketDetail
    extra = 0
    # readonly_fields = ('full_name', 'phone', 'count', 'created_at')
    # can_delete = False


# Ticket modelining admin registratsiyasi
@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = (
        'id',
        'driver',
        'direction',
        'status',
        'passenger_count',
        'created_at',
    )
    list_display_links = ('id', 'driver')
    list_filter = ('status', 'direction')
    inlines = [TicketDetailInline]

    def passenger_count(self, obj):
        return obj.details.aggregate(total=Sum('count'))['total'] or 0

    passenger_count.short_description = 'Yo‘lovchilar soni'