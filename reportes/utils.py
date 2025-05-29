from fpdf import FPDF
from io import BytesIO

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de propiedades - Colombia Realty HUB', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, num, title):
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, f'{num}. {title}', 0, 1, 'L')

    def chapter_body(self, text):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, text)
        self.ln()

    def add_propiedad(self, i, propiedad):
        self.chapter_title(i, propiedad.get("Tipo de Inmueble", "Tipo desconocido"))
        descripcion = f"Ciudad: {propiedad.get('Ciudad', 'N/A')}, Barrio: {propiedad.get('Barrio', 'N/A')}, Estrato: {propiedad.get('Estrato', 'N/A')}\n"
        descripcion += f"Precio: {propiedad.get('Precio', 'N/A')}, Área: {propiedad.get('Área Construida', 'N/A')} m2\n"
        descripcion += f"Habitaciones: {propiedad.get('Habitaciones', 'N/A')}, Baños: {propiedad.get('Baños', 'N/A')}\n"
        descripcion += f"Enlace: {propiedad.get('Enlace', 'N/A')}"
        self.chapter_body(descripcion)

def generar_reporte_pdf(lista_propiedades):
    pdf = PDF()
    pdf.add_page()

    for i, prop in enumerate(lista_propiedades, 1):
        pdf.add_propiedad(i, prop)

    return pdf.output(dest='S').encode('latin1')
