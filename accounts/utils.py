from django.utils import timezone

from .models import TokenWallet, TokenTransaction


def give_daily_tokens(user):

    wallet, created = TokenWallet.objects.get_or_create(
        user=user
    )

    today = timezone.localdate()

    if wallet.last_daily_reward != today:

        wallet.balance += 20

        wallet.last_daily_reward = today

        wallet.save()

        TokenTransaction.objects.create(
            wallet=wallet,
            amount=20,
            transaction_type="daily",
            description="Bonus quotidien de 20 jetons"
        )

    return wallet