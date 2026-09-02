import re
from datetime import date, datetime


class ValidationError(ValueError):
    pass


def validar_required(data, fields, prefix=''):
    missing = [f for f in fields if not data.get(f)]
    if missing:
        raise ValidationError(f'Campos requeridos faltantes: {", ".join(prefix + f for f in missing)}')


def validar_fecha(valor, nombre='fecha', permitir_pasado=True):
    if not valor:
        return None
    if isinstance(valor, (date, datetime)):
        fecha = valor if isinstance(valor, date) else valor.date()
    elif isinstance(valor, str):
        fecha = None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                fecha = datetime.strptime(valor, fmt).date()
                break
            except ValueError:
                continue
        if not fecha:
            raise ValidationError(f'{nombre} con formato invalido. Use AAAA-MM-DD')
    else:
        raise ValidationError(f'{nombre} debe ser una fecha valida')

    if not permitir_pasado and fecha < date.today():
        raise ValidationError(f'{nombre} no puede ser anterior a hoy')
    return fecha


def validar_rango_fechas(inicio, fin, nombre='Periodo'):
    if inicio and fin and inicio > fin:
        raise ValidationError(f'{nombre}: fecha_fin debe ser posterior a fecha_inicio')


def validar_ci(ci, nombre='CI'):
    if not ci:
        return
    if not re.match(r'^\d{4,15}$', str(ci)):
        raise ValidationError(f'{nombre} debe contener solo digitos (4-15 caracteres)')


def validar_email(email, nombre='Email'):
    if not email:
        return
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(email)):
        raise ValidationError(f'{nombre} no tiene un formato valido')


def validar_telefono(telefono, nombre='Telefono'):
    if not telefono:
        return
    limpio = re.sub(r'[\s\-\(\)\+]', '', str(telefono))
    if not limpio.isdigit() or len(limpio) < 7:
        raise ValidationError(f'{nombre} debe tener al menos 7 digitos')


def validar_rude(rude):
    if not rude:
        raise ValidationError('RUDE es requerido')
    if not re.match(r'^[A-Za-z0-9]{5,20}$', str(rude)):
        raise ValidationError('RUDE debe contener 5-20 caracteres alfanumericos')


def validar_gestion(gestion):
    if not gestion:
        raise ValidationError('Gestion es requerida')
    try:
        g = int(gestion)
        if g < 2000 or g > 2100:
            raise ValidationError('Gestion debe estar entre 2000 y 2100')
    except (TypeError, ValueError):
        raise ValidationError('Gestion debe ser un numero entero')


def validar_puntaje_maximo(puntaje, nombre='Puntaje'):
    if puntaje is not None:
        try:
            p = float(puntaje)
            if p <= 0 or p > 1000:
                raise ValidationError(f'{nombre} debe estar entre 1 y 1000')
        except (TypeError, ValueError):
            raise ValidationError(f'{nombre} debe ser un numero')


def validar_nombre(texto, nombre='Nombre', max_len=200):
    if texto and len(str(texto)) > max_len:
        raise ValidationError(f'{nombre} no debe exceder {max_len} caracteres')


def validar_nota(valor, nombre='Nota'):
    if valor is not None:
        try:
            v = float(valor)
            if v < 0 or v > 100:
                raise ValidationError(f'{nombre} debe estar entre 0 y 100')
        except (TypeError, ValueError):
            raise ValidationError(f'{nombre} debe ser un numero')


def validar_dia_semana(dia):
    try:
        d = int(dia)
        if d < 1 or d > 7:
            raise ValidationError('Dia de semana debe ser 1 (Lunes) a 7 (Domingo)')
    except (TypeError, ValueError):
        raise ValidationError('Dia de semana debe ser un numero')


def validar_hora(valor, nombre='Hora'):
    if not valor:
        return
    if not re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', str(valor)):
        raise ValidationError(f'{nombre} debe tener formato HH:MM')
