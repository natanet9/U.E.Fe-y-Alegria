ROLES = {
    "director": {
        "email": "director@panama.com",
        "password": "test1234",
        "nombre": "Director Test",
    },
    "secretaria": {
        "email": "secretaria@panama.com",
        "password": "test1234",
        "nombre": "Secretaria Test",
    },
    "docente": {
        "email": "docente@panama.com",
        "password": "test1234",
        "nombre": "Docente Test",
    },
    "regente": {
        "email": "regente@panama.com",
        "password": "test1234",
        "nombre": "Regente Test",
    },
    "tutor": {
        "email": "tutor@panama.com",
        "password": "test1234",
        "nombre": "Tutor Test",
    },
}

ENDPOINTS = {
    "dashboard": "/api/dashboard/",
    "courses_detail": "/api/courses/detail/",
    "courses_asignaciones": "/api/courses/asignaciones/",
    "grades": "/api/grades/",
    "activities": "/api/activities/",
    "activities_notes": "/api/activities/notes/",
    "attendance": "/api/attendance/",
    "attendance_calendar": "/api/attendance/calendar/",
    "reports": "/api/reports/",
    "periods": "/api/periods/",
    "dimension_config": "/api/dimension-config/",
    "enrollment_search": "/api/enrollment/search/",
    "enrollment_catalogs": "/api/enrollment/catalogs/",
    "students_list": "/api/students/",
}

PERMISSIONS = {
    "director": [
        "dashboard", "courses_detail", "courses_asignaciones", "grades",
        "activities", "activities_notes", "attendance", "attendance_calendar",
        "reports", "periods", "dimension_config", "enrollment_search",
        "enrollment_catalogs", "students_list",
    ],
    "secretaria": [
        "dashboard", "courses_detail", "courses_asignaciones", "grades",
        "activities", "activities_notes", "attendance", "attendance_calendar",
        "reports", "periods", "dimension_config", "enrollment_search",
        "enrollment_catalogs", "students_list",
    ],
    "docente": [
        "dashboard", "courses_detail", "courses_asignaciones", "grades",
        "activities", "activities_notes", "attendance", "attendance_calendar",
        "reports",
    ],
    "regente": [
        "dashboard", "courses_detail", "courses_asignaciones", "grades",
        "activities", "activities_notes", "attendance", "attendance_calendar",
        "reports", "periods", "dimension_config", "enrollment_search",
        "enrollment_catalogs", "students_list",
    ],
    "tutor": [
        "dashboard", "courses_detail", "courses_asignaciones", "grades",
        "activities", "activities_notes",
    ],
}
