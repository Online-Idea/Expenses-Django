from ..accounts.models import AccountClient, Salon


def salons_processor(request):
    salons = []
    if request.user.is_authenticated:
        # Так как request.user уже является экземпляром Client, мы можем напрямую использовать его
        account_client = AccountClient.objects.filter(account=request.user)

        salons = Salon.objects.filter(client=account_client[0].client)
    return {'salons': salons}
