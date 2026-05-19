from django.contrib import admin

from .models import Payment, Plan, Subscription, TransactionLog


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "setup_price", "monthly_price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("client", "plan", "project", "status", "current_period_end", "cancel_at_period_end")
    list_filter = ("status", "cancel_at_period_end", "created_at")
    search_fields = ("client__company_name", "client__user__email", "stripe_subscription_id")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("client", "project", "kind", "status", "amount", "currency", "paid_at", "created_at")
    list_filter = ("kind", "status", "currency", "created_at")
    search_fields = ("client__company_name", "stripe_checkout_session_id", "stripe_payment_intent_id", "stripe_invoice_id")


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "status", "client", "project", "amount", "currency", "created_at")
    list_filter = ("provider", "event_type", "status", "created_at")
    search_fields = ("stripe_event_id", "event_type", "client__company_name", "project__name")
    readonly_fields = ("payload",)
