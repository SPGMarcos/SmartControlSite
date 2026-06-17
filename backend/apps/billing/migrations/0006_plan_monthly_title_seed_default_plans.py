from decimal import Decimal

from django.db import migrations, models


DEFAULT_PLANS = [
    {
        "name": "Start",
        "slug": "start",
        "setup_price": Decimal("799.00"),
        "monthly_price": Decimal("99.00"),
        "monthly_title": "Assinatura opcional de suporte",
        "description": "Hospedagem, manutencao, seguranca e pequenos ajustes mensais.",
        "features": ["Landing page", "Hospedagem assistida", "Painel do cliente"],
    },
    {
        "name": "Business",
        "slug": "business",
        "setup_price": Decimal("1990.00"),
        "monthly_price": Decimal("249.00"),
        "monthly_title": "Operacao recorrente",
        "description": "Suporte, atualizacoes, melhorias de performance e acompanhamento.",
        "features": ["Site completo", "SEO tecnico", "Suporte mensal"],
    },
    {
        "name": "Scale",
        "slug": "scale",
        "setup_price": Decimal("0.00"),
        "monthly_price": Decimal("0.00"),
        "monthly_title": "SLA e evolucao continua",
        "description": "Roadmap, automacoes, integracoes e suporte prioritario.",
        "features": ["Sistema web", "Integracoes", "SLA prioritario"],
    },
]


def seed_default_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    for item in DEFAULT_PLANS:
        Plan.objects.update_or_create(
            slug=item["slug"],
            defaults={
                **item,
                "is_active": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0005_supabase_user_billing_links"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="monthly_title",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.RunPython(seed_default_plans, migrations.RunPython.noop),
    ]
