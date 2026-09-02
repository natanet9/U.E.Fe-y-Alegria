import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    BaseDocTemplate,
)

from ..tracing import trace_service_class
from .access_service import AccessControlService
from .report_card_service import ReportCardService


@trace_service_class
class ReportCardPDFService:

    def __init__(self):
        self.ac = AccessControlService()
        self._rcs = ReportCardService()

    def generar_pdf(self, usuario, estudiante_id, gestion=None):
        data = self._rcs.generar_boletin(usuario, estudiante_id, gestion)
        return self._build_pdf(data)

    def _build_pdf(self, data):
        buf = io.BytesIO()
        doc = BaseDocTemplate(
            buf,
            pagesize=LETTER,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
        )
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='normal',
        )
        doc.addPageTemplates([PageTemplate(id='main', frames=frame)])

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title2', parent=styles['Title'],
            fontSize=14, spaceAfter=6, alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            'Subtitle', parent=styles['Normal'],
            fontSize=10, alignment=TA_CENTER, spaceAfter=12,
        )
        section_style = ParagraphStyle(
            'Section', parent=styles['Heading2'],
            fontSize=11, spaceBefore=12, spaceAfter=6,
            textColor=colors.HexColor('#1a5276'),
        )
        normal = styles['Normal']

        story = []

        story.append(Paragraph('UNIDAD EDUCATIVA PANAMA', title_style))
        story.append(Paragraph(f'BOLETA DE CALIFICACIONES', subtitle_style))
        story.append(Spacer(1, 6))

        est = data['estudiante']
        estudiante_info = (
            f'<b>Estudiante:</b> {est["nombres"]} {est["primer_apellido"]} {est["segundo_apellido"]}<br/>'
            f'<b>RUDE:</b> {est["rude"]} | <b>CI:</b> {est["ci"]}<br/>'
            f'<b>Curso:</b> {data["curso"]["nombre"]} | <b>Gestion:</b> {data["gestion"]}'
        )
        story.append(Paragraph(estudiante_info, normal))
        story.append(Spacer(1, 12))

        periodos = data['periodos']
        periodo_headers = [Paragraph(p['nombre'], ParagraphStyle(
            'PH', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER,
        )) for p in periodos]

        col_widths = [1.8 * inch] + [0.8 * inch] * len(periodos) + [0.8 * inch]
        header_row = [Paragraph('<b>Area/Materia</b>', ParagraphStyle(
            'H', parent=styles['Normal'], fontSize=8, alignment=TA_LEFT,
        ))] + periodo_headers + [Paragraph('<b>Promedio</b>', ParagraphStyle(
            'H', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER,
        ))]

        table_data = [header_row]
        for mat in data['materias']:
            row = [
                Paragraph(mat['area'], ParagraphStyle('R', parent=styles['Normal'], fontSize=8)),
            ]
            for p in periodos:
                val = mat['notas_por_periodo'].get(str(p['id']))
                row.append(Paragraph(
                    f'{val:.2f}' if val is not None else '-',
                    ParagraphStyle('C', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER),
                ))
            prom = mat['promedio_final']
            row.append(Paragraph(
                f'{prom:.2f}' if prom is not None else '-',
                ParagraphStyle('C', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER),
            ))
            table_data.append(row)

        if table_data:
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t)

        story.append(Spacer(1, 12))

        story.append(Paragraph('Asistencia por Periodo', section_style))
        asist_headers = ['Periodo', 'Total', 'Presentes', '% Asistencia']
        asist_data = [asist_headers]
        for a in data['asistencias']:
            asist_data.append([
                a['periodo'],
                str(a['total']),
                str(a['presentes']),
                f'{a["porcentaje"]}%',
            ])
        asist_table = Table(asist_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 1*inch])
        asist_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(asist_table)

        if data.get('observaciones'):
            story.append(Spacer(1, 12))
            story.append(Paragraph('Observaciones', section_style))
            for obs in data['observaciones']:
                story.append(Paragraph(
                    f'<b>{obs["periodo"]} - {obs["area"]}:</b> '
                    f'{obs["observacion"]} ({obs.get("indicador", "")})',
                    ParagraphStyle('Obs', parent=styles['Normal'], fontSize=8, spaceAfter=2),
                ))

        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes
