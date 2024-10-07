from django.http import HttpRequest
from typing import Dict, List
from ..accounts.models import AccountClient, Salon


def salons_processor(request: HttpRequest) -> Dict[str, List[Salon]]:
    """
    Контекстный процессор для получения списка салонов, принадлежащих текущему пользователю.

    :param request: объект HttpRequest, содержащий информацию о текущем пользователе
    :return: Словарь с ключом 'salons', содержащий список салонов для текущего клиента
    """
    salons = []

    if request.user.is_authenticated:
        # Получаем AccountClient для текущего пользователя
        account_client = AccountClient.objects.filter(account=request.user)

        # Если найден AccountClient, получаем салоны, связанные с клиентом
        if account_client.exists():
            salons = Salon.objects.filter(client=account_client[0].client)

    # Возвращаем салоны в виде словаря для использования в контексте шаблона
    return {'salons': salons}
