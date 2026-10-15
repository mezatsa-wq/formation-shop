from django.core.management.base import BaseCommand
from accounts.models import TokenWallet


class Command(BaseCommand):
    help = "Attribue les récompenses quotidiennes de jetons."

    def handle(self, *args, **options):
        credited = 0

        for wallet in TokenWallet.objects.all().iterator():
            if wallet.give_daily_reward():
                credited += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Traitement terminé : {credited} portefeuille(s) crédité(s)."
            )
        )