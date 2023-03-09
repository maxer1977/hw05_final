import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    current_date = datetime.date.today()
    return {'year': current_date.year}
