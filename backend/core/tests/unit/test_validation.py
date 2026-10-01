import pytest
from datetime import date, datetime

from core.services.validation import (
    ValidationError,
    validar_ci,
    validar_dia_semana,
    validar_email,
    validar_fecha,
    validar_gestion,
    validar_hora,
    validar_nombre,
    validar_nota,
    validar_puntaje_maximo,
    validar_rango_fechas,
    validar_required,
    validar_rude,
    validar_telefono,
)


def test_validar_required_raises_with_missing_fields():
    with pytest.raises(ValidationError, match='Campos requeridos faltantes: email, rol'):
        validar_required({}, ['email', 'rol'])


def test_validar_required_supports_prefix():
    with pytest.raises(ValidationError, match='usuario_email'):
        validar_required({}, ['email'], prefix='usuario_')


def test_validar_fecha_accepts_date_and_datetime():
    assert validar_fecha(date(2026, 5, 1)) == date(2026, 5, 1)
    assert validar_fecha(datetime(2026, 5, 1, 12, 30)).year == 2026


def test_validar_fecha_accepts_common_strings():
    assert validar_fecha('2026-05-01') == date(2026, 5, 1)
    assert validar_fecha('01/05/2026') == date(2026, 5, 1)
    assert validar_fecha('2026/05/01') == date(2026, 5, 1)


def test_validar_fecha_rejects_invalid_type_and_format():
    with pytest.raises(ValidationError, match='fecha con formato invalido'):
        validar_fecha('05-01-2026')
    with pytest.raises(ValidationError, match='fecha debe ser una fecha valida'):
        validar_fecha(123)


def test_validar_rango_fechas_rejects_inverted_range():
    with pytest.raises(ValidationError, match='fecha_fin debe ser posterior a fecha_inicio'):
        validar_rango_fechas(date(2026, 5, 2), date(2026, 5, 1))


@pytest.mark.parametrize(
    'value,validator,pattern',
    [
        ('abcd', validar_ci, 'CI debe contener solo digitos'),
        ('bad@email', validar_email, 'Email no tiene un formato valido'),
        ('123', validar_telefono, 'Telefono debe tener al menos 7 digitos'),
        ('bad rude', validar_rude, 'RUDE debe contener 5-20 caracteres alfanumericos'),
        (1999, validar_gestion, 'Gestion debe ser un numero entero'),
        ('abc', validar_gestion, 'Gestion debe ser un numero entero'),
        (0, validar_puntaje_maximo, 'Puntaje debe ser un numero'),
        ('abc', validar_puntaje_maximo, 'Puntaje debe ser un numero'),
        (101, validar_nota, 'Nota debe ser un numero'),
        ('abc', validar_nota, 'Nota debe ser un numero'),
        (0, validar_dia_semana, 'Dia de semana debe ser un numero'),
        ('abc', validar_dia_semana, 'Dia de semana debe ser un numero'),
        ('99', validar_hora, 'Hora debe tener formato HH:MM'),
        ('x' * 201, validar_nombre, 'Nombre no debe exceder 200 caracteres'),
    ],
)
def test_validators_reject_invalid_values(value, validator, pattern):
    with pytest.raises(ValidationError, match=pattern):
        validator(value)


def test_validators_allow_empty_optional_values():
    assert validar_ci(None) is None
    assert validar_email('') is None
    assert validar_telefono(None) is None
    assert validar_puntaje_maximo(None) is None
    assert validar_nota(None) is None
    assert validar_hora(None) is None
    assert validar_nombre(None) is None
