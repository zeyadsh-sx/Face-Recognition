# services/export_service.py

import csv
import json
import os
from datetime import datetime

try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

class ExportService:

    def export_to_csv(self, data, filename="export.csv"):
        try:
            if not data:
                return False, "No data"

            filepath = self._ensure_dir(filename)
            keys = list(data[0].keys())

            with open(filepath, "w", newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)

            return True, filepath

        except Exception as e:
            return False, str(e)

    def export_to_excel(self, data, filename="export.xlsx"):
        try:
            if not data:
                return False, "No data"

            filepath = self._ensure_dir(filename)
            if not filepath.lower().endswith(('.xlsx', '.xls')):
                filepath += '.xlsx'

            if OPENPYXL_AVAILABLE and filepath.lower().endswith('.xlsx'):
                workbook = Workbook()
                sheet = workbook.active
                headers = list(data[0].keys())
                sheet.append(headers)
                for row in data:
                    sheet.append([row.get(key, '') for key in headers])
                workbook.save(filepath)
                return True, filepath

            if filepath.lower().endswith('.xlsx'):
                fallback_path = os.path.splitext(filepath)[0] + '.xls'
            else:
                fallback_path = filepath

            xml = self._build_spreadsheet_xml(data)
            with open(fallback_path, 'w', encoding='utf-8') as f:
                f.write(xml)

            return True, fallback_path

        except Exception as e:
            return False, str(e)

    def export_to_pdf(self, data, filename="export.pdf", title="Attendance Report"):
        try:
            if not data:
                return False, "No data"

            filepath = self._ensure_dir(filename)
            if not filepath.lower().endswith('.pdf'):
                filepath += '.pdf'

            return self._export_pdf_simple(data, filepath, title)

        except Exception as e:
            return False, str(e)

    def _ensure_dir(self, filename):
        directory = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        return filename

    def _escape_xml_value(self, value):
        if value is None:
            return ''
        escaped = str(value)
        escaped = escaped.replace('&', '&amp;')
        escaped = escaped.replace('<', '&lt;')
        escaped = escaped.replace('>', '&gt;')
        escaped = escaped.replace('"', '&quot;')
        escaped = escaped.replace("'", '&apos;')
        return escaped

    def _build_spreadsheet_xml(self, data):
        headers = list(data[0].keys())
        xml_lines = [
            '<?xml version="1.0"?>',
            '<?mso-application progid="Excel.Sheet"?>',
            '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"',
            ' xmlns:o="urn:schemas-microsoft-com:office:office"',
            ' xmlns:x="urn:schemas-microsoft-com:office:excel"',
            ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">',
            '  <Worksheet ss:Name="Report">',
            '    <Table>'
        ]

        xml_lines.append('      <Row>')
        for header in headers:
            xml_lines.append(f'        <Cell><Data ss:Type="String">{self._escape_xml_value(header)}</Data></Cell>')
        xml_lines.append('      </Row>')

        for row in data:
            xml_lines.append('      <Row>')
            for key in headers:
                xml_lines.append(f'        <Cell><Data ss:Type="String">{self._escape_xml_value(row.get(key, ""))}</Data></Cell>')
            xml_lines.append('      </Row>')

        xml_lines.extend([
            '    </Table>',
            '  </Worksheet>',
            '</Workbook>'
        ])

        return '\n'.join(xml_lines)

    def _escape_pdf_text(self, text):
        if text is None:
            return ''
        string = str(text)
        string = string.replace('\\', '\\\\')
        string = string.replace('(', '\\(')
        string = string.replace(')', '\\)')
        string = string.replace('\n', '\\n')
        return string

    def _export_pdf_simple(self, data, filepath, title):
        lines = [title, '']
        headers = list(data[0].keys())
        header_line = ' | '.join(headers)
        lines.append(header_line)
        lines.append('-' * len(header_line))

        for row in data:
            lines.append(' | '.join(str(row.get(key, '')) for key in headers))

        page_width = 595
        page_height = 842
        margin = 40
        line_height = 14
        max_lines = int((page_height - margin * 2) / line_height) - 2

        if len(lines) > max_lines:
            lines = lines[:max_lines - 1] + ['... truncated ...']

        content_stream = 'BT\n/F1 10 Tf\n'
        content_stream += f'1 0 0 1 {margin} {page_height - margin} Tm\n'
        for line in lines:
            text = self._escape_pdf_text(line)
            content_stream += f'({text}) Tj\n0 -{line_height} Td\n'
        content_stream += 'ET\n'

        content_bytes = content_stream.encode('latin-1', errors='replace')
        length = len(content_bytes)

        def make_obj(number, body):
            if isinstance(body, bytes):
                return f'{number} 0 obj\n'.encode('latin-1') + body + b'endobj\n'
            return f'{number} 0 obj\n{body}endobj\n'.encode('latin-1')

        objects = []
        objects.append(make_obj(1, '<< /Type /Catalog /Pages 2 0 R >>\n'))
        objects.append(make_obj(2, '<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n'))
        page_body = (
            '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
            '/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\n'
        )
        objects.append(make_obj(3, page_body))
        objects.append(make_obj(4, '<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\n'))
        objects.append(make_obj(5, f'<< /Length {length} >>\nstream\n'.encode('latin-1') + content_bytes + b'endstream\n'))

        pdf_bytes = bytearray()
        pdf_bytes.extend(b'%PDF-1.4\n')

        offsets = []
        for obj in objects:
            offsets.append(len(pdf_bytes))
            pdf_bytes.extend(obj)

        xref_start = len(pdf_bytes)
        pdf_bytes.extend(f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'.encode('latin-1'))
        for offset in offsets:
            pdf_bytes.extend(f'{offset:010d} 00000 n \n'.encode('latin-1'))

        pdf_bytes.extend(f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n'.encode('latin-1'))
        pdf_bytes.extend(str(xref_start).encode('latin-1'))
        pdf_bytes.extend(b'\n%%EOF\n')

        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)

        return True, filepath

    def export_to_generic(self, data, filename):
        """Generic export function that detects format from extension"""
        try:
            if filename.endswith('.json'):
                return self.export_to_json(data, filename)
            elif filename.endswith('.csv'):
                return self.export_to_csv(data, filename)
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                return self.export_to_excel(data, filename)
            elif filename.endswith('.pdf'):
                return self.export_to_pdf(data, filename)
            else:
                return False, f"Unsupported format: {filename}"
        except Exception as e:
            return False, f"Generic export error: {str(e)}"

    def export_to_json(self, data, filename="export.json"):
        try:
            filepath = self._ensure_dir(filename)
            with open(filepath, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            return True, filepath
        
        except Exception as e:
            return False, str(e)