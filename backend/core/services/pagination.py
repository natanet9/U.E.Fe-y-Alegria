from math import ceil


def paginar(qs, page=1, page_size=20, max_page_size=100):
    """
    Pagina un QuerySet y devuelve datos paginados.
    """
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(1, int(page_size)), max_page_size)
    except (TypeError, ValueError):
        page_size = 20

    total = qs.count()
    total_pages = max(1, ceil(total / page_size))
    page = min(page, total_pages) if total > 0 else 1
    offset = (page - 1) * page_size
    items = list(qs[offset:offset + page_size])

    return {
        'items': items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }


def paginar_desde_queryset(qs, page=1, page_size=20, max_page_size=100):
    """
    Versión que devuelve el QuerySet paginado directamente (para lazy evaluation).
    """
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(1, int(page_size)), max_page_size)
    except (TypeError, ValueError):
        page_size = 20

    total = qs.count()
    total_pages = max(1, ceil(total / page_size))
    page = min(page, total_pages) if total > 0 else 1
    offset = (page - 1) * page_size

    return {
        'items': qs[offset:offset + page_size],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }
