from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("billing", "0004_rename_billing_pay_client_idx_payments_client__49e10c_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="plano",
            field=models.CharField(blank=True, max_length=140),
        ),
        migrations.AddField(
            model_name="subscription",
            name="stripe_customer_id",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="subscription",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="subscriptions", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="payment",
            name="stripe_payment_intent",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="payments", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["user"], name="subscription_user_id_9d52cc_idx"),
        ),
        migrations.AddIndex(
            model_name="subscription",
            index=models.Index(fields=["stripe_customer_id"], name="subscription_stripe__4a40d2_idx"),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["user"], name="payments_user_id_4b8ec1_idx"),
        ),
    ]
