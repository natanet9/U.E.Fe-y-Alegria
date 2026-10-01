import pytest
from datetime import date

from core.services.validation import (
    validar_required,
    validar_fecha,
    validar_rango_fechas,
    validar_ci,
    validar_email,
    validar_telefono,
    validar_rude,
    validar_gestion,
    validar_puntaje_maximo,
    validar_nombre,
    validar_nota,
    validar_dia_semana,
    validar_hora,
    ValidationError,
)


def test_validar_required_raises_when_missing():
    with pytest.raises(ValidationError):
        validar_required({'a': 1}, ['a', 'b'])


def test_validar_fecha_formats_and_none():
    assert validar_fecha(None) is None
    assert validar_fecha('2026-05-28') == date(2026, 5, 28)
    assert validar_fecha('28/05/2026') == date(2026, 5, 28)
    with pytest.raises(ValidationError):
        validar_fecha('05-28-2026')


def test_validar_rango_fechas():
    with pytest.raises(ValidationError):
        validar_rango_fechas(date(2026, 5, 2), date(2026, 5, 1))


def test_validar_ci_and_email():
    validar_ci('1234')
    with pytest.raises(ValidationError):
        validar_ci('12ab')

    validar_email('a@b.com')
    with pytest.raises(ValidationError):
        validar_email('not-an-email')


def test_validar_telefono_rude_gestion():
    validar_telefono('123-4567')
    with pytest.raises(ValidationError):
        validar_telefono('12')

    with pytest.raises(ValidationError):
        validar_rude('bad!')
    validar_rude('ABC12')

    with pytest.raises(ValidationError):
        validar_gestion('x')
    with pytest.raises(ValidationError):
        validar_gestion(1999)
    validar_gestion(2026)


def test_validar_puntaje_nombre_nota_dia_hora():
    validar_puntaje_maximo(10)
    with pytest.raises(ValidationError):
        validar_puntaje_maximo(0)
    with pytest.raises(ValidationError):
        validar_puntaje_maximo('abc')

    validar_nombre('ok')
    long_name = 'x' * 201
    with pytest.raises(ValidationError):
        validar_nombre(long_name)

    validar_nota(50)
    with pytest.raises(ValidationError):
        validar_nota(200)

    validar_dia_semana(1)
    with pytest.raises(ValidationError):
        validar_dia_semana(0)

    validar_hora('09:30')
    with pytest.raises(ValidationError):
        validar_hora('9-30')
