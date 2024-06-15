from django import forms
from pdf2image import convert_from_path
import pytesseract

class DocumentForm(forms.Form):
    document_url = forms.URLField(label='Document URL', required=False)
    document_file = forms.FileField(label='Document File', required=False)

    def clean(self):
        cleaned_data = super().clean()
        document_url = cleaned_data.get("document_url")
        document_file = cleaned_data.get("document_file")

        if not document_url and not document_file:
            raise forms.ValidationError("You must provide either a document URL or a document file.")
        return cleaned_data
    
class InvoiceUploadForm(forms.Form):
    file = forms.FileField()    
    
    # Tesseract OCR'ın tam yolunu belirleyin (eğer PATH'e eklenmediyse)
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def process_invoice(pdf_path):
        try:
            # PDF dosyasını görüntülere dönüştür
            images = convert_from_path(pdf_path)
            ocr_results = []

            # Her bir görüntü üzerinde OCR işlemi yap
            for image in images:
                text = pytesseract.image_to_string(image)
                ocr_results.append(text)
            
            return ocr_results
        except Exception as e:
            return str(e)

    # PDF dosya yolunu belirtin
    pdf_path = r'C:\Users\31621\Desktop\P21-DjangoTweet-main\merinos 492854 19-04-2024.pdf'
    result = process_invoice(pdf_path)

    # OCR sonuçlarını yazdır
    for page_num, page_text in enumerate(result, start=1):
        print(f"Page {page_num} OCR Results:")
        print(page_text)
        print("\n" + "-"*50 + "\n")    
 
class UploadFileForm(forms.Form):
    file = forms.FileField()        
    
class DocumentForm(forms.Form):
    document_url = forms.URLField(required=False)
    document_file = forms.FileField(required=False)    
