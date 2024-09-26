from .models import Salon


def salons_processor(request):
    salons = []
    if request.user.is_authenticated:
        # Так как request.user уже является экземпляром Client, мы можем напрямую использовать его
        salons = Salon.objects.filter(client=request.user)
    return {'salons': salons}
