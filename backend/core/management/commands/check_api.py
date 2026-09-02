from django.core.management.base import BaseCommand
from django.urls import get_resolver
from rest_framework.test import APIClient
from django.conf import settings
from core.models import Usuarios, Roles
# import sample models to build safe payloads
from core.models import DocenteAsignacion, Estudiantes, Cursos, Periodos
from core.auth_utils import build_token
import re
import json


class Command(BaseCommand):
    help = 'Check API endpoints by making requests as seeded users'

    def handle(self, *args, **options):
        resolver = get_resolver()
        # core urls are included under /api/ so we'll load core.urls patterns
        try:
            from core import urls as core_urls
            patterns = getattr(core_urls, 'urlpatterns', [])
        except Exception as e:
            self.stderr.write(f'Error loading core.urls: {e}')
            return

        # prepare sample ids for safe non-destructive payloads
        sample_ids = {}
        try:
            da = DocenteAsignacion.objects.filter(activo=True).first()
            sample_ids['docente_asignacion_id'] = da.id if da else None
        except Exception:
            sample_ids['docente_asignacion_id'] = None

        try:
            est = Estudiantes.objects.filter().first()
            sample_ids['estudiante_id'] = est.id if est else None
        except Exception:
            sample_ids['estudiante_id'] = None

        try:
            curso = Cursos.objects.filter(activo=True).first()
            sample_ids['curso_id'] = curso.id if curso else None
        except Exception:
            sample_ids['curso_id'] = None

        try:
            periodo = Periodos.objects.filter(activo=True).first()
            sample_ids['periodo_id'] = periodo.id if periodo else None
        except Exception:
            sample_ids['periodo_id'] = None

        try:
            actividad = __import__('core.models', fromlist=['Actividades']).Actividades.objects.filter(activo=True).first()
            sample_ids['actividad_id'] = actividad.id if actividad else None
        except Exception:
            sample_ids['actividad_id'] = None

        # prepare clients for roles
        emails = [
            'director@uepanama.com',
            'secretaria@uepanama.com',
            'regente@uepanama.com',
            'docente1@uepanama.com',
            'docente2@uepanama.com',
        ]

        clients = {'anonymous': APIClient()}
        # Ensure host header on anonymous client before login attempts
        clients['anonymous'].defaults['HTTP_HOST'] = 'localhost'
        for email in emails:
            try:
                Usuarios.objects.get(email=email)  # ensure user exists
                # Attempt login to obtain a valid token via the real login flow
                anon = clients['anonymous']
                try:
                    login_resp = anon.post('/api/auth/login/', {'email': email, 'password': '123456'}, format='json')
                    token = None
                    try:
                        token = login_resp.json().get('token')
                    except Exception:
                        token = None
                except Exception:
                    token = None

                if not token:
                    self.stdout.write(f'Could not obtain token for {email}; login status: {getattr(login_resp, "status_code", "?" )}')
                    continue

                client = APIClient()
                # Ensure host header to avoid DisallowedHost during tests
                client.defaults['HTTP_HOST'] = 'localhost'
                # Use Authorization header with token obtained from login
                client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
                clients[email] = client
            except Usuarios.DoesNotExist:
                self.stdout.write(f'User {email} not found in DB; skipping')
        # anonymous client already has HTTP_HOST set

        report = []

        def concretize(route):
            # replace converters like <int:foo> or <str:bar>
            s = route
            s = re.sub(r"<int:[^>]+>", "1", s)
            s = re.sub(r"<str:[^>]+>", "test", s)
            s = re.sub(r"<slug:[^>]+>", "test", s)
            # ensure leading and trailing slashes
            if not s.startswith('/'):
                s = '/' + s
            if not s.endswith('/'):
                s = s + '/'
            return '/api' + s

        for p in patterns:
            try:
                route = getattr(p.pattern, '_route', None) or str(p.pattern)
                url = concretize(route)
            except Exception:
                continue

            for identity, client in clients.items():
                # try GET first
                try:
                    resp = client.get(url)
                except Exception as e:
                    report.append({'url': url, 'identity': identity, 'error': str(e)})
                    continue

                entry = {'url': url, 'identity': identity, 'status': resp.status_code, 'method': 'GET'}
                # try to include json keys if possible
                try:
                    entry['body'] = resp.json()
                except Exception:
                    entry['body'] = resp.content.decode('utf-8', errors='replace')[:1000]

                # map safe POST payloads for known endpoints (by substring)
                def build_login_payload(identity):
                    # use provided identity email if it's a real user
                    if identity != 'anonymous':
                        return {'email': identity, 'password': '123456'}
                    return {'email': 'director@uepanama.com', 'password': '123456'}

                POST_PAYLOAD_BY_SUBSTR = {
                    '/auth/login/': lambda ident: build_login_payload(ident),
                    '/schedules/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                        'dia_semana': 1,
                        'hora_inicio': '08:00:00',
                        'hora_fin': '09:00:00',
                    },
                    '/grades/recompute-actividades/': lambda ident: {},
                    '/actividades/notas-estudiante/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                        'estudiante_id': sample_ids.get('estudiante_id'),
                    },
                    '/actividades/notas/': lambda ident: {
                        'actividad_id': sample_ids.get('actividad_id'),
                        # notas: mapping estudiante_id -> valor
                        'notas': {sample_ids.get('estudiante_id'): 85.0} if sample_ids.get('estudiante_id') else {},
                    },
                    '/actividades/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                        'nombre': 'Chequeo API',
                        'puntaje_maximo': 10.0,
                        'fecha_actividad': '2026-05-01',
                    },
                    '/attendance/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                        'fecha': '2026-05-29',
                        # estados: mapping estudiante_id -> estado
                        'estados': {sample_ids.get('estudiante_id'): 'presente'} if sample_ids.get('estudiante_id') else {},
                    },
                    '/courses/detail/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                    },
                }

                # map safe GET query params for known endpoints that return 400 without them
                GET_QUERY_PARAMS_BY_SUBSTR = {
                    '/actividades/notas-estudiante/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                        'estudiante_id': sample_ids.get('estudiante_id'),
                    },
                    '/actividades/notas/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                    },
                    '/actividades/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                    },
                    '/attendance/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                    },
                    '/grades/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                        'periodo_id': sample_ids.get('periodo_id'),
                    },
                    '/courses/detail/': lambda ident: {
                        'docente_asignacion_id': sample_ids.get('docente_asignacion_id'),
                    },
                    '/enrollment/search-tutor/': lambda ident: {
                        'ci': '1234567',
                    },
                    '/enrollment/search/': lambda ident: {
                        'rude': '00000000',
                    },
                    '/report-card/': lambda ident: {
                        'estudiante_id': sample_ids.get('estudiante_id')
                    },
                    '/report-card/download/': lambda ident: {
                        'estudiante_id': sample_ids.get('estudiante_id')
                    },
                }

                PUT_PAYLOAD_BY_SUBSTR = {
                    '/schedules/': lambda ident: {},
                    '/students/': lambda ident: {},
                    '/docentes/': lambda ident: {},
                    '/courses/': lambda ident: {},
                    '/dimension-config/': lambda ident: {},
                    '/actividades/': lambda ident: {},
                    '/attendance/': lambda ident: {},
                    '/licencias/': lambda ident: {},
                    '/students/': lambda ident: {
                        'estado': 'activo'
                    },
                    '/docentes/': lambda ident: {
                        'activo': True
                    },
                    '/actividades/': lambda ident: {
                        'nombre': 'Actualiza API',
                    },
                }

                # substrings that must be skipped (destructive or side-effects)
                SKIP_POST_SUBSTRINGS = [
                    '/auth/logout',
                    '/auth/refresh',
                    '/auth/change-password',
                    '/auth/forgot-password',
                    '/auth/reset-password',
                    '/cierre',
                    '/report-card/download',
                    '/report-card/download/',
                    '/report-card/',
                    '/download',
                    '/marcar-enviado',
                    '/restore',
                    '/save/',
                    '/save',
                ]

                def should_try_post(u):
                    for s in SKIP_POST_SUBSTRINGS:
                        if s in u:
                            return False
                    return True

                # If GET not allowed, try POST with a safe payload when possible
                if resp.status_code == 405 and should_try_post(url):
                    # probe OPTIONS to discover allowed methods when available
                    allow_methods = None
                    try:
                        opt = client.options(url)
                        allow = opt.get('Allow') if isinstance(opt, dict) else opt.headers.get('Allow')
                        if allow:
                            allow_methods = [m.strip().upper() for m in allow.split(',')]
                    except Exception:
                        allow_methods = None
                    # find matching payload builder
                    payload = None
                    for key, builder in POST_PAYLOAD_BY_SUBSTR.items():
                        if key in url:
                            try:
                                payload = builder(identity)
                            except Exception:
                                payload = {}
                            break

                    # fallback: try POST with empty payload only if a builder was found
                    if payload is not None:
                        try:
                            # only attempt POST if OPTIONS suggests POST is allowed (or if OPTIONS not available)
                            if allow_methods is None or 'POST' in allow_methods:
                                resp2 = client.post(url, payload)
                            else:
                                resp2 = None
                            entry['status_post'] = resp2.status_code
                            entry['method_post'] = 'POST'
                            try:
                                entry['body_post'] = resp2.json()
                            except Exception:
                                entry['body_post'] = resp2.content.decode('utf-8', errors='replace')[:1000]
                            if resp2.status_code < 400:
                                entry['status'] = resp2.status_code
                                entry['method'] = 'POST'
                                entry['body'] = entry['body_post']
                        except Exception as e:
                            entry['post_error'] = str(e)
                    else:
                        entry['note'] = 'POST skipped (no safe payload defined)'

                if resp.status_code == 405 and should_try_post(url):
                    put_payload = None
                    for key, builder in PUT_PAYLOAD_BY_SUBSTR.items():
                        if key in url:
                            try:
                                put_payload = builder(identity)
                            except Exception:
                                put_payload = {}
                            break

                    if put_payload is not None:
                        try:
                            # attempt PUT only if OPTIONS suggests PUT/PATCH is allowed
                            tried_put = False
                            resp3 = None
                            if allow_methods is None or 'PUT' in allow_methods:
                                resp3 = client.put(url, put_payload, format='json')
                                tried_put = True
                            # try PATCH as fallback if PUT not allowed but PATCH is
                            if (not tried_put) and (allow_methods is None or 'PATCH' in allow_methods):
                                resp3 = client.patch(url, put_payload, format='json')
                                tried_put = True
                            entry['status_put'] = resp3.status_code
                            entry['method_put'] = 'PUT'
                            try:
                                entry['body_put'] = resp3.json()
                            except Exception:
                                entry['body_put'] = resp3.content.decode('utf-8', errors='replace')[:1000]
                            if resp3.status_code < 400 and entry.get('status', 405) >= 400:
                                entry['status'] = resp3.status_code
                                entry['method'] = 'PUT'
                                entry['body'] = entry['body_put']
                        except Exception as e:
                            entry['put_error'] = str(e)

                # If GET returned 400 (missing required params), try adding safe query params
                if resp.status_code == 400:
                    try:
                        params = None
                        for key, builder in GET_QUERY_PARAMS_BY_SUBSTR.items():
                            if key in url:
                                try:
                                    params = builder(identity)
                                except Exception:
                                    params = None
                                break

                        if params:
                            try:
                                resp_q = client.get(url, params, format='json')
                                entry['status_get_with_params'] = resp_q.status_code
                                try:
                                    entry['body_get_with_params'] = resp_q.json()
                                except Exception:
                                    entry['body_get_with_params'] = resp_q.content.decode('utf-8', errors='replace')[:1000]
                                if resp_q.status_code < 400:
                                    entry['status'] = resp_q.status_code
                                    entry['method'] = 'GET'
                                    entry['body'] = entry['body_get_with_params']
                            except Exception as e:
                                entry['get_params_error'] = str(e)
                        else:
                            entry.setdefault('note', 'GET 400: no query-builder defined')
                    except Exception as e:
                        entry['get_params_error'] = str(e)

                report.append(entry)

        out = json.dumps(report, indent=2, ensure_ascii=False)
        self.stdout.write(out)
        # also write to a file for later inspection
        with open('api_check_report.json', 'w', encoding='utf-8') as f:
            f.write(out)
        self.stdout.write(self.style.SUCCESS('API check completed; report saved to api_check_report.json'))
