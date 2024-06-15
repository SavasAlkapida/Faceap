from django.shortcuts import render, redirect
from django.conf import settings
from .forms import DocumentForm
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from .forms import InvoiceUploadForm
from .models import Invoice, InvoiceItem
import os
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from django.http import JsonResponse
from .forms import UploadFileForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.conf import settings
from .forms import DocumentForm
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
from azure.core.exceptions import HttpResponseError
import re
import base64
from celery import shared_task
import requests


def parse_invoice_text(text):
    invoice_data = {
        "company": "",
        "date": "",
        "invoice_number": "",
        "customer": "",
        "items": [],
        "total_amount": "",
        "iban": ""
    }

    # Şirket adını ayıkla
    company_match = re.search(r'Firma:\s*(.*)', text)
    if company_match:
        invoice_data["company"] = company_match.group(1).strip()

    # Müşteri adını ayıkla
    customer_match = re.search(r'Alkapida\s*BV', text)
    if customer_match:
        invoice_data["customer"] = "Alkapida BV"

    # Tarihi ayıkla
    date_match = re.search(r'Datum\s*(\d{2}\.\d{2}\.\d{4})', text)
    if date_match:
        invoice_data["date"] = date_match.group(1)

    # Fatura numarasını ayıkla
    invoice_number_match = re.search(r'Rechnungs-Nr\.\s*(\d+)', text)
    if invoice_number_match:
        invoice_data["invoice_number"] = invoice_number_match.group(1)

    # Ürünleri ayıkla
    item_matches = re.findall(r'(.*?)\s+(\d{2}\.\d{2}\.\d{4})\s*(\d+)\s+([0-9,]+)\s+([0-9,]+)\s+([0-9,]+)', text)
    for match in item_matches:
        item = {
            "description": match[0].strip(),
            "quantity": match[2],
            "unit_price": match[3].replace(',', '.'),
            "total_price": match[5].replace(',', '.')
        }
        invoice_data["items"].append(item)
    
    # Toplam tutarı ayıkla
    total_amount_match = re.search(r'Gesamtsumme\s*([0-9,]+)', text)
    if total_amount_match:
        invoice_data["total_amount"] = total_amount_match.group(1).replace(',', '.')
    
    # IBAN numarasını ayıkla
    iban_match = re.search(r'IBAN:\s*(\w+)', text)
    if iban_match:
        invoice_data["iban"] = iban_match.group(1)
    
    return invoice_data

def process_invoice(file_path):
    results = {}
    try:
        # PDF dosyasını resimlere dönüştür
        images = convert_from_path(file_path)
        
        ocr_text = ""
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            ocr_text += text
            print(f"Page {i + 1} OCR Results: {text}")
        
        results = parse_invoice_text(ocr_text)
        print(f"Parsed Results: {results}")
    except Exception as e:
        results['error'] = str(e)
    
    return results
    

def success_view(request):
    results = request.session.get('results', None)
    return render(request, 'ocrapp/success.html', {'results': results})

# Diğer fonksiyonlarınız burada olacak    

def format_bounding_region(bounding_regions):
    if not bounding_regions:
        return "N/A"
    return ", ".join(
        "Page #{}: {}".format(region.page_number, format_polygon(region.polygon))
        for region in bounding_regions
    )

def format_polygon(polygon):
    if not polygon:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in polygon])

def analyze_layout(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_url = form.cleaned_data['document_url']
            document_file = form.cleaned_data['document_file']

            document_analysis_client = DocumentAnalysisClient(
                endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT, 
                credential=AzureKeyCredential(settings.AZURE_FORM_RECOGNIZER_KEY)
            )

            if document_url:
                poller = document_analysis_client.begin_analyze_document_from_url(
                    "prebuilt-layout", document_url
                )
            else:
                poller = document_analysis_client.begin_analyze_document(
                    "prebuilt-layout", document_file.read()
                )

            result = poller.result()

            analysis_results = []
            words_list = []

            for idx, style in enumerate(result.styles):
                analysis_results.append(
                    "Document contains {} content".format(
                        "handwritten" if style.is_handwritten else "no handwritten"
                    )
                )

            for page in result.pages:
                analysis_results.append("----Analyzing layout from page #{}----".format(page.page_number))
                analysis_results.append(
                    "Page has width: {} and height: {}, measured with unit: {}".format(
                        page.width, page.height, page.unit
                    )
                )

                for line_idx, line in enumerate(page.lines):
                    words = line.get_words()
                    analysis_results.append(
                        "...Line # {} has word count {} and text '{}' within bounding box '{}'".format(
                            line_idx,
                            len(words),
                            line.content,
                            format_polygon(line.polygon),
                        )
                    )

                    for word in words:
                        analysis_results.append(
                            "......Word '{}' has a confidence of {}".format(
                                word.content, word.confidence
                            )
                        )
                        words_list.append(word.content)

                for selection_mark in page.selection_marks:
                    analysis_results.append(
                        "...Selection mark is '{}' within bounding box '{}' and has a confidence of {}".format(
                            selection_mark.state,
                            format_polygon(selection_mark.polygon),
                            selection_mark.confidence,
                        )
                    )

            for table_idx, table in enumerate(result.tables):
                analysis_results.append(
                    "Table # {} has {} rows and {} columns".format(
                        table_idx, table.row_count, table.column_count
                    )
                )
                for region in table.bounding_regions:
                    analysis_results.append(
                        "Table # {} location on page: {} is {}".format(
                            table_idx,
                            region.page_number,
                            format_polygon(region.polygon),
                        )
                    )
                for cell in table.cells:
                    analysis_results.append(
                        "...Cell[{}][{}] has content '{}'".format(
                            cell.row_index,
                            cell.column_index,
                            cell.content,
                        )
                    )
                    for region in cell.bounding_regions:
                        analysis_results.append(
                            "...content on page {} is within bounding box '{}'".format(
                                region.page_number,
                                format_polygon(region.polygon),
                            )
                        )

            return render(request, 'ocrapp/invoice_analysis_result.html', {
                'result': analysis_results,
                'words': words_list
            })
    else:
        form = DocumentForm()

    return render(request, 'ocrapp/upload.html', {'form': form})

def analyze_invoice(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_url = form.cleaned_data['document_url']
            document_file = form.cleaned_data['document_file']

            document_analysis_client = DocumentAnalysisClient(
                endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT, 
                credential=AzureKeyCredential(settings.AZURE_FORM_RECOGNIZER_KEY)
            )

            if document_url:
                poller = document_analysis_client.begin_analyze_document_from_url(
                    "prebuilt-invoice", document_url
                )
            else:
                poller = document_analysis_client.begin_analyze_document(
                    "prebuilt-invoice", document_file.read()
                )

            result = poller.result()

            analysis_results = []
            for idx, invoice in enumerate(result.documents):
                analysis_results.append("--------Recognizing invoice #{}--------".format(idx + 1))
                for field, value in invoice.fields.items():
                    if value:
                        analysis_results.append(
                            "{}: {} has confidence: {}".format(
                                field, value.value, value.confidence
                            )
                        )

            return render(request, 'invoice_analysis_result.html', {
                'result': analysis_results,
            })
    else:
        form = DocumentForm()

    return render(request, 'upload.html', {'form': form})

def analyze_elio_sentences(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_url = form.cleaned_data['document_url']
            document_file = form.cleaned_data['document_file']

            document_analysis_client = DocumentAnalysisClient(
                endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT, 
                credential=AzureKeyCredential(settings.AZURE_FORM_RECOGNIZER_KEY)
            )

            if document_url:
                poller = document_analysis_client.begin_analyze_document_from_url(
                    "prebuilt-invoice", document_url
                )
            else:
                poller = document_analysis_client.begin_analyze_document(
                    "prebuilt-invoice", document_file.read()
                )

            result = poller.result()

            elio_sentences = []

            def extract_elio_sentences(value):
                if isinstance(value.value, str) and value.value.startswith("Elio"):
                    elio_sentences.append(value.value)

            for idx, invoice in enumerate(result.documents):
                for field, value in invoice.fields.items():
                    if value:
                        extract_elio_sentences(value)

                if invoice.fields.get("Items"):
                    for idx, item in enumerate(invoice.fields.get("Items").value):
                        for subfield, subvalue in item.value.items():
                            if subvalue:
                                extract_elio_sentences(subvalue)

            return render(request, 'ocrapp/elio_sentences.html', {
                'sentences': elio_sentences,
            })
    else:
        form = DocumentForm()

    return render(request, 'ocrapp/upload.html', {'form': form})

def upload_invoice(request):
    if request.method == 'POST':
        form = InvoiceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            if os.path.exists(file_path):
                results = process_invoice(file_path)
                print(f"Results: {results}")
                request.session['results'] = results
                return redirect('analyze_invoice_view')  # 'success_view' yerine 'analyze_invoice_view' kullanın
            else:
                raise FileNotFoundError(f'Dosya bulunamadı: {file_path}')
    else:
        form = InvoiceUploadForm()
    return render(request, 'ocrapp/upload.html', {'form': form})


def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'ocrapp/invoice_list.html', {'invoices': invoices})

import pytesseract
from PIL import Image




def process_invoice(file_path):
    results = {}
    try:
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_FORM_RECOGNIZER_KEY)
        )
        
        with open(file_path, "rb") as fd:
            document_content = fd.read()
        
        base64_document = base64.b64encode(document_content).decode('utf-8')

        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-invoice",
            AnalyzeDocumentRequest(base64_source=base64_document)
        )
        
        result = poller.result()
        
        for idx, invoice in enumerate(result.documents):
            vendor_name = invoice.fields.get("VendorName")
            results["company"] = vendor_name.value if vendor_name else ""
            invoice_date = invoice.fields.get("InvoiceDate")
            results["date"] = invoice_date.value if invoice_date else ""
            invoice_id = invoice.fields.get("InvoiceId")
            results["invoice_number"] = invoice_id.value if invoice_id else ""
            customer_name = invoice.fields.get("CustomerName")
            results["customer"] = customer_name.value if customer_name else ""
            total_amount = invoice.fields.get("InvoiceTotal")
            results["total_amount"] = total_amount.value if total_amount else ""
            iban = invoice.fields.get("VendorIBAN")
            results["iban"] = iban.value if iban else ""

            items = invoice.fields.get("Items")
            results["items"] = []
            if items:
                for item in items.value:
                    item_details = {
                        "description": "",
                        "quantity": "",
                        "unit_price": "",
                        "total_price": ""
                    }
                    description = item.value.get("Description")
                    quantity = item.value.get("Quantity")
                    unit_price = item.value.get("UnitPrice")
                    total_price = item.value.get("Amount")

                    if description:
                        item_details["description"] = description.value
                    if quantity:
                        item_details["quantity"] = quantity.value
                    if unit_price:
                        item_details["unit_price"] = unit_price.value
                    if total_price:
                        item_details["total_price"] = total_price.value

                    results["items"].append(item_details)
                    
    except Exception as e:
        results['error'] = str(e)
    
    return results


def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'ocrapp/invoice_list.html', {'invoices': invoices})



def get_words(page, line):
    result = []
    for word in page.words:
        if _in_span(word, line.spans):
            result.append(word)
    return result

def _in_span(word, spans):
    for span in spans:
        if word.span.offset >= span.offset and (word.span.offset + word.span.length) <= (span.offset + span.length):
            return True
    return False

def analyze_layout_view(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_url = form.cleaned_data.get('document_url')
            document_file = request.FILES.get('document_file')

            document_intelligence_client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_FORM_RECOGNIZER_KEY)
            )

            if document_url:
                poller = document_intelligence_client.begin_analyze_document_from_url(
                    "prebuilt-layout", document_url
                )
            elif document_file:
                poller = document_intelligence_client.begin_analyze_document(
                    "prebuilt-layout", document_file.read()
                )
            else:
                return JsonResponse({"error": "No document provided"}, status=400)

            result = poller.result()
            analysis_results = []

            for idx, style in enumerate(result.styles):
                analysis_results.append(
                    "Document contains {} content".format(
                        "handwritten" if style.is_handwritten else "no handwritten"
                    )
                )

            for page in result.pages:
                analysis_results.append("----Analyzing layout from page #{}----".format(page.page_number))
                analysis_results.append(
                    "Page has width: {} and height: {}, measured with unit: {}".format(
                        page.width, page.height, page.unit
                    )
                )

                for line_idx, line in enumerate(page.lines):
                    words = [word.content for word in line.words]
                    analysis_results.append(
                        "...Line # {} has word count {} and text '{}' within bounding polygon '{}'".format(
                            line_idx, len(words), line.content, line.polygon
                        )
                    )

                for selection_mark in page.selection_marks:
                    analysis_results.append(
                        "...Selection mark is '{}' within bounding polygon '{}' and has a confidence of {}".format(
                            selection_mark.state, selection_mark.polygon, selection_mark.confidence
                        )
                    )

            for table_idx, table in enumerate(result.tables):
                analysis_results.append(
                    "Table # {} has {} rows and {} columns".format(
                        table_idx, table.row_count, table.column_count
                    )
                )
                for region in table.bounding_regions:
                    analysis_results.append(
                        "Table # {} location on page: {} is {}".format(
                            table_idx, region.page_number, region.polygon
                        )
                    )
                for cell in table.cells:
                    analysis_results.append(
                        "...Cell[{}][{}] has text '{}'".format(
                            cell.row_index, cell.column_index, cell.content
                        )
                    )

            return render(request, 'ocrapp/invoice_list.html', {
                'result': analysis_results
            })
    else:
        form = DocumentForm()

    return render(request, 'ocrapp/upload.html', {'form': form})

def analyze_invoice_view(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document_url = form.cleaned_data.get('document_url')
            document_file = request.FILES.get('document_file')

            document_intelligence_client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_FORM_RECOGNIZER_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_FORM_RECOGNIZER_KEY)
            )

            try:
                if document_url:
                    poller = document_intelligence_client.begin_analyze_document_from_url(
                        model_id="prebuilt-invoice",
                        document_url=document_url
                    )
                elif document_file:
                    document_bytes = document_file.read()
                    poller = document_intelligence_client.begin_analyze_document(
                        model_id="prebuilt-invoice",
                        document=document_bytes
                    )
                else:
                    return JsonResponse({"error": "No document provided"}, status=400)

                result = poller.result()
                analysis_results = {
                    "company": "",
                    "date": "",
                    "invoice_number": "",
                    "customer": "",
                    "items": [],
                    "total_amount": "",
                    "iban": ""
                }

                for idx, invoice in enumerate(result.documents):
                    vendor_name = invoice.fields.get("VendorName")
                    if vendor_name:
                        analysis_results["company"] = vendor_name.value
                    invoice_date = invoice.fields.get("InvoiceDate")
                    if invoice_date:
                        analysis_results["date"] = invoice_date.value
                    invoice_id = invoice.fields.get("InvoiceId")
                    if invoice_id:
                        analysis_results["invoice_number"] = invoice_id.value
                    customer_name = invoice.fields.get("CustomerName")
                    if customer_name:
                        analysis_results["customer"] = customer_name.value
                    total_amount = invoice.fields.get("InvoiceTotal")
                    if total_amount:
                        analysis_results["total_amount"] = total_amount.value
                    iban = invoice.fields.get("VendorIBAN")
                    if iban:
                        analysis_results["iban"] = iban.value

                    items = invoice.fields.get("Items")
                    if items:
                        for item in items.value:
                            item_details = {
                                "description": "",
                                "quantity": "",
                                "unit_price": "",
                                "total_price": ""
                            }
                            description = item.value.get("Description")
                            quantity = item.value.get("Quantity")
                            unit_price = item.value.get("UnitPrice")
                            total_price = item.value.get("Amount")

                            if description:
                                item_details["description"] = description.value
                            if quantity:
                                item_details["quantity"] = quantity.value
                            if unit_price:
                                item_details["unit_price"] = unit_price.value
                            if total_price:
                                item_details["total_price"] = total_price.value

                            analysis_results["items"].append(item_details)

                # Sonuçları template'e gönderin
                return render(request, 'ocrapp/analysis_results.html', {
                    'result': analysis_results
                })

            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

    else:
        form = DocumentForm()

    return render(request, 'ocrapp/invoice_analysis_result.html', {'form': form})

