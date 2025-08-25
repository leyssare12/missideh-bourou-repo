import os.path
from datetime import datetime
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.lorem_ipsum import paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Spacer, SimpleDocTemplate, Paragraph, Table, TableStyle, Frame, PageTemplate, KeepInFrame
from reportlab.pdfgen import canvas

from BTest import settings
from Bapp.models import PDFManager

#PDFS_PATH = Path.home() / "Desktop/MissidheBourou/PDF"
# Récupère le chemin depuis la variable d'environnement ou utilise un chemin par défaut
PDFS_PATH = Path(settings.PDFS_ROOT)
LOGO_IMAGE = settings.MEDIA_ROOT / "images/profile_pictures/logo_b289906d-56b1-44f8-8472-a5fb7bc4947f.png"

class PDFGenerator:
    def __init__(self, title, auteur=None, paragraph=None,):
        self.styles = getSampleStyleSheet()
        # Création des styles personnalisés
        self.custom_styles = {
            'Footer': ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=8,
                alignment=1,
            ),
            'Header': ParagraphStyle(
                'Header',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#4256e5'),
                spaceAfter=30,
            ),
            'Title': ParagraphStyle(
                'Title',
                parent=self.styles['Heading1'],
                fontSize=16,
                textColor=colors.black,
                alignment=1,
                spaceAfter=30,
            )
        }
        self.auteur = auteur if auteur else "Missidhé Bourou"
        self.title = title
        self.paragraph = paragraph
        self.spacer = Spacer(1, 12)
        self.date_ajout = datetime.now().strftime("%d/%m/%Y")
        self.directory = PDFS_PATH
        if not self.directory.exists():
            self.directory.mkdir()

        # Chemins des ressources
        #self.logo_path = Path("/home/bombilafou/Documents/Pyton/Bourotest/src/Bapp/static/images/logo.png")
        self.logo_path = LOGO_IMAGE
        if not self.logo_path.exists():
            raise FileNotFoundError("Le fichier logo.png n'existe pas.")

    def _header(self, canvas, document):
        """Gestion de l'en-tête"""
        canvas.saveState()
        # Ajout du logo
        if self.logo_path.exists():
            canvas.drawImage(
                str(self.logo_path),
                30,
                A4[1] - 80,
                width=50,
                height=50,
                preserveAspectRatio=True
            )

        # Titre du document
        canvas.setFont('Helvetica-Bold', 16)
        canvas.drawString(100, A4[1] - 50, self.title)

        # Date
        canvas.setFont('Helvetica', 8)
        canvas.drawString(450, A4[1] - 30, f"Date: {self.date_ajout}")
        # Auteur
        canvas.setFont('Helvetica', 8)
        canvas.drawString(450, A4[1] - 50, f"Auteur: {self.auteur}")

        # Ligne de séparation
        canvas.line(30, A4[1] - 85, A4[0] - 30, A4[1] - 85)
        canvas.restoreState()

    def _footer(self, canvas, document):
        """Gestion du pied de page"""
        canvas.saveState()
        # Numéro de page
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.setFont("Helvetica", 9)
        canvas.drawString(A4[0] / 2 - 20, 30, text)

        # Informations de pied de page
        footer_text = "Missidhé Bourou - Tous droits réservés"
        canvas.setFont("Helvetica", 8)
        canvas.drawString(30, 15, footer_text)

        canvas.restoreState()

    def pdfs_file_generator_save(self, data, headers):
        pdf_fil_name = f"{self.title}.pdf"
        destination = os.path.join(self.directory, pdf_fil_name)

        # Configuration du document
        document = SimpleDocTemplate(
            destination,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=100,
            bottomMargin=50,
        )

        # Configuration des frames et template
        frame = Frame(
            document.leftMargin,
            document.bottomMargin,
            A4[0] - document.leftMargin - document.rightMargin,
            A4[1] - document.topMargin - document.bottomMargin,
            id='normal'
        )

        template = PageTemplate(
            id='main_template',
            frames=[frame],
            onPage=lambda canvas, document: (self._header(canvas, document), self._footer(canvas, document))
        )
        document.addPageTemplates([template])

        # Contenu du document
        elements = []

        # Paragraphe descriptif du document
        paragraph = self.paragraph
        elements.append(Paragraph(paragraph, self.custom_styles['Header']))
        elements.append(self.spacer)

        # Préparation des données du tableau

        rows = [[item[i] for i in range(len(headers))] for item in data]


        table_data = [headers] + rows
        # Calcul de la largeur disponible
        available_width = A4[0] - document.leftMargin - document.rightMargin

        # Calcul des largeurs optimales des colonnes
        col_widths = self.calculate_column_widths(data, headers, available_width)

        # Création et style du tableau
        table = Table(
            table_data,
            colWidths=col_widths,
            hAlign='LEFT'
        )

        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4256e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8e8e8')]),

            # Lignes horizontales plus fines
            ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.black),  # Lignes horizontales internes
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black),  # Ligne supérieure du tableau
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.black),  # Ligne inférieure du tableau

            # Lignes verticales plus fines
            ('LINEBEFORE', (0, 0), (0, -1), 0.5, colors.black),  # Première ligne verticale
            ('LINEAFTER', (-1, 0), (-1, -1), 0.5, colors.black),  # Dernière ligne verticale
            ('LINEBEFORE', (1, 0), (-1, -1), 0.25, colors.black),  # Lignes verticales internes

        ]))

        elements.append(table)

        try:
            document.build(elements)
            print(f"Le document {pdf_fil_name} a été créé avec succès.")
            return str(destination)
        except Exception as e:
            print(f"Erreur lors de la création du PDF: {str(e)}")
            return None

    def pdfs_file_generator(self, data, headers):
        pdf_fil_name = f"{self.title}.pdf"
        destination = os.path.join(self.directory, pdf_fil_name)

        # Configuration simplifiée du document
        document = SimpleDocTemplate(
            destination,
            pagesize=A4,
            leftMargin=30,
            rightMargin=30,
            topMargin=100,
            bottomMargin=50
        )


        # Configuration des frames et template
        frame = Frame(
            document.leftMargin,
            document.bottomMargin,
            A4[0] - document.leftMargin - document.rightMargin,
            A4[1] - document.topMargin - document.bottomMargin,
            id='normal'
        )

        template = PageTemplate(
            id='main_template',
            frames=[frame],
            onPage=lambda canvas, document: (self._header(canvas, document), self._footer(canvas, document))
        )
        document.addPageTemplates([template])

        # Styles
        styles = getSampleStyleSheet()
        cell_style = styles['Normal']
        cell_style.fontName = 'Helvetica'
        cell_style.fontSize = 8
        cell_style.leading = 9
        cell_style.alignment = 1  # Centré

        # Fonction de préparation du contenu avec contrôle strict
        def safe_cell_content(text, max_chars=50, max_lines=3):
            text = str(text)[:max_chars * max_lines]  # Limite absolue
            chunks = [text[i:i + max_chars] for i in range(0, min(len(text), max_chars * max_lines), max_chars)]
            return Paragraph("<br/>".join(chunks[:max_lines]), cell_style)

        # Préparation des données
        table_data = [[safe_cell_content(header) for header in headers]]  # En-têtes
        for row in data:
            table_data.append([safe_cell_content(str(cell)) for cell in row])

        # Création du tableau avec largeurs fixes
        col_widths = [document.width / len(headers)] * len(headers)  # Distribution égale
        table = Table(table_data, colWidths=col_widths, hAlign='LEFT')
        # Style minimal et robuste
        table.setStyle(TableStyle([
            # Style de l'en-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),  # Bleu moderne
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Texte en blanc
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Police en gras pour l'en-tête
            ('FONTSIZE', (0, 0), (-1, 0), 10),  # Taille plus grande pour l'en-tête
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Style du contenu
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),  # Espacement uniforme
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),  # Espacement uniforme

            # Alignement
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alignement vertical au centre

            # Couleurs alternées des lignes
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),  # Gris plus subtil

            # Bordures externes
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),  # Bordure externe grise

            # Lignes horizontales internes
            ('LINEBELOW', (0, 0), (-1, 0), 1.0, colors.HexColor('#1a73e8')),  # Ligne sous l'en-tête plus visible
            ('LINEBELOW', (0, 1), (-1, -1), 0.1, colors.HexColor('#e0e0e0')),
            # Lignes horizontales plus fines et plus claires

            # Lignes verticales
            ('LINEAFTER', (0, 0), (-2, -1), 0.1, colors.HexColor('#e0e0e0')),
            # Lignes verticales plus fines et plus claires

            # Espacement des cellules
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))

        # Construction du document
        try:
            document.build([table])
            print(str(destination))
            return str(destination)
        except Exception as e:
            print(f"Erreur PDF: {str(e)}")
            return None

    def calculate_column_widths(self, data, headers, available_width):
        # Calculer la largeur maximale de chaque colonne basée sur le contenu
        max_widths = [0] * len(headers)

        # Vérifier les en-têtes
        for i, header in enumerate(headers):
            max_widths[i] = max(max_widths[i], len(str(header)) * 7)  # 7 pixels par caractère approximativement

        # Vérifier toutes les données
        for row in data:
            for i, cell in enumerate(row):
                max_widths[i] = max(max_widths[i], len(str(cell)) * 7)

        # Ajuster les largeurs pour ne pas dépasser la largeur disponible
        total_width = sum(max_widths)
        if total_width > available_width:
            ratio = available_width / total_width
            max_widths = [width * ratio for width in max_widths]

        return max_widths


#Gestionnaire d'affichage et de téléchargement de PDFs
class PDFView:

    @staticmethod
    def liste_pdfs(request):
        """
        Affiche la liste des PDFs selon le rôle de l'utilisateur
        """
        template = 'site/documents/pdf_listings.html'

        try:
            # Pour l'admin, on montre tous les PDFs
            if request.user.role == 'ADMIN':
                pdf_files = PDFManager.objects.all().order_by('-created_at')
            else:
                # Pour les autres, uniquement leurs PDFs
                pdf_files = PDFManager.objects.filter(
                    created_by=request.user
                ).order_by('-created_at')

            # Préparer les données pour l'affichage
            pdfs = []
            for pdf in pdf_files:
                pdfs.append({
                    'id': pdf.id,
                    'nom': pdf.title,
                    'description': pdf.description,
                    'date_creation': pdf.created_at,
                    'createur': pdf.created_by.prenoms,
                    'type': pdf.document_type,
                    'url': reverse('Bapp:download_pdf', kwargs={'pdf_id': pdf.id})
                })

            context = {
                'pdfs': pdfs,
                'total_pdfs': len(pdfs)
            }

            return render(request, template_name=template, context=context)

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors du chargement des PDFs: {str(e)}")
            return render(request, template_name=template, context={'pdfs': [], 'total_pdfs': 0})

    @staticmethod
    def download_pdf(request, pdf_id):
        """
        Permet le téléchargement d'un PDF spécifique
        """
        try:
            # Récupérer le PDF par son ID
            pdf = PDFManager.objects.get(id=pdf_id)

            # Vérifier les permissions
            if not request.user.role == 'ADMIN' and pdf.created_by != request.user:
                raise PermissionDenied("Vous n'avez pas la permission de télécharger ce fichier")

            # Vérifier que le fichier existe
            if not pdf.file:
                raise FileNotFoundError("Le fichier PDF n'existe pas")

            # Préparer la réponse
            response = FileResponse(
                pdf.file.open('rb'),
                content_type='application/pdf'
            )

            # Définir si le fichier doit être téléchargé ou affiché dans le navigateur
            if request.GET.get('download') == 'true':
                response['Content-Disposition'] = f'attachment; filename="{pdf.title}.pdf"'
            else:
                response['Content-Disposition'] = f'inline; filename="{pdf.title}.pdf"'

            return response

        except PDFManager.DoesNotExist:
            messages.error(request, "Le PDF demandé n'existe pas")
            return redirect('Bapp:documents_pdf')
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('Bapp:documents_pdf')
        except Exception as e:
            messages.error(request, f"Une erreur est survenue: {str(e)}")
            return redirect('Bapp:documents_pdf')

    @staticmethod
    def delete_pdf(request, pdf_id):
        """
        Permet la suppression d'un PDF spécifique
        """
        try:
            # Récupérer le PDF par son ID
            pdf = PDFManager.objects.get(id=pdf_id)

            # Vérifier les permissions
            if not request.user.role == 'ADMIN' and pdf.created_by != request.user:
                raise PermissionDenied("Vous n'avez pas la permission de supprimer ce fichier")

            # Vérifier que le fichier existe
            if not pdf.file:
                raise FileNotFoundError("Le fichier PDF n'existe pas")

            # Supprimer le fichier physique
            if pdf.file:
                pdf.file.delete()

            # Supprimer l'enregistrement de la base de données
            pdf.delete()

            messages.success(request, "Le fichier PDF a été supprimé avec succès")
            return redirect('Bapp:documents_pdf')  # Rediriger vers la liste des PDFs

        except PDFManager.DoesNotExist:
            messages.error(request, "Le fichier PDF demandé n'existe pas")
            return redirect('Bapp:documents_pdf')
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('Bapp:documents_pdf')
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de la suppression : {str(e)}")
            return redirect('Bapp:documents_pdf')