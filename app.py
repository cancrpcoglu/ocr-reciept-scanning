from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import cv2
import numpy as np
import re

# OCR konumu
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

app = Flask(__name__)
CORS(app)

@app.route("/upload", methods=["POST"])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "image dosyası eksik"}), 700

    files = request.files.getlist("image")
    results = []
    for file in files:
        try:
            print(f"İşleniyor: {file.filename}")
            img = Image.open(file)

            # Preprocessing
            img = img.convert("L")
            img = ImageEnhance.Contrast(img).enhance(2)
            img = img.filter(ImageFilter.SHARPEN)
            img = img.resize((img.width * 2, img.height * 2))

            img_np = np.array(img)
            denoised = cv2.fastNlMeansDenoising(img_np, None, 30, 7, 21)
            img = Image.fromarray(denoised)

            # OCR
            text = pytesseract.image_to_string(img, lang="tur+eng")
            format_type = detect_format(text)

            if format_type == "e_arsiv":
                parsed_data = filter_ocr_e_arsiv(text)
            elif format_type == "pos_fis":
                parsed_data = filter_ocr_pos_fis(text)
            else:
                parsed_data = filter_ocr_klasik_fis(text)

            results.append({
                "filename": file.filename,
                "ocr_text": text,
                "parsed": parsed_data
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })

    return jsonify({"ocr_results": results})

# ----------------------------
# Format belirleme
# ----------------------------
def detect_format(text):
    if "E-ARŞİV FATURA BİLGİ FİŞİ" in text or "GMU 507" in text:
        return "e_arsiv"
    if "TÜRKİYE İŞ BANKASI" in text.upper() and "PAYWAVE" in text.upper():
        return "pos_fis"
    return "klasik_fis"

# ----------------------------
# Klasik fiş parser
# ----------------------------
def filter_ocr_klasik_fis(text):
    tarih_match = re.search(r'(\d{2}[\/\.-]\d{2}[\/\.-]\d{4})', text)
    saat_match = re.search(r'(\d{2}:\d{2}:\d{2})', text)
    tutar_match = re.search(r'([\d]{1,3}(?:[.,]\d{3})*[.,]\d{2})', text)

    tarih = tarih_match.group(1) if tarih_match else "Tarih düzgün okunamıyor"
    saat = saat_match.group(1) if saat_match else "Saat düzgün okunamıyor"
    toplam_tutar = tutar_match.group(1) if tutar_match else "Toplam tutar düzgün okunamıyor"

    try:
        if toplam_tutar and "düzgün" not in toplam_tutar:
            clean = toplam_tutar.replace(".", "").replace(",", ".")
            if float(clean) < 1:
                toplam_tutar = "Toplam tutar düzgün okunamıyor"
    except:
        toplam_tutar = "Toplam tutar düzgün okunamıyor"

    lines = text.splitlines()
    firma = extract_firma_klasik_fis(lines)
    if not firma or "ARA TOPLAM" in firma.upper():
        firma = "Firma adı düzgün okunamıyor"

    return {
        "firma": firma,
        "tarih": tarih,
        "saat": saat,
        "toplam_tutar": toplam_tutar,
    }


def extract_firma_klasik_fis(lines):
    keywords = ['TİC', 'LTD', 'ŞTİ', 'MARKET', 'AVM', 'MAĞAZA', 'GIDA', 'TİCARET', 'TEKSTİL']
    for i in range(len(lines)):
        upper_line = lines[i].upper()
        if any(keyword in upper_line for keyword in keywords):
            if i > 0:
                return lines[i - 1].strip()
    for line in lines:
        if line.isupper() and len(line.split()) >= 2:
            return line.strip()
    return "Firma adı düzgün okunamıyor"

# ----------------------------
# E-arşiv parser
# ----------------------------
def filter_ocr_e_arsiv(text):
    lines = text.splitlines()
    firma = extract_firma_e_arsiv(lines)

    tarih = None
    saat = None
    for line in lines:
        if 'tarih' in line.lower() or 'saat' in line.lower():
            found_dates = re.findall(r'(\d{2}[\/\.-]\d{2}[\/\.-]\d{4})', line)
            found_times = re.findall(r'(\d{2}:\d{2})', line)
            if found_dates:
                tarih = found_dates[0]
            if found_times:
                saat = found_times[0]
        if tarih and saat:
            break

    if not tarih:
        tarih = "Tarih düzgün okunamıyor"
    if not saat:
        saat = "Saat düzgün okunamıyor"

    tutar = None
    for line in lines[::-1]:
        match = re.search(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*TL', line.upper())
        if match:
            tutar = match.group(1)
            break

    try:
        if tutar:
            clean = tutar.replace(".", "").replace(",", ".")
            if float(clean) < 1:
                tutar = "Toplam tutar düzgün okunamıyor"
    except:
        tutar = "Toplam tutar düzgün okunamıyor"

    if not tutar:
        tutar = "Toplam tutar düzgün okunamıyor"

    return {
        "firma": firma,
        "tarih": tarih,
        "saat": saat,
        "toplam_tutar": tutar
    }

def extract_firma_e_arsiv(lines):
    keywords = ['TİC', 'LTD', 'ŞTİ', 'MARKET', 'AVM', 'MAĞAZA', 'GIDA', 'TİCARET', 'TEKSTİL']
    for line in lines:
        upper_line = line.upper()
        for keyword in keywords:
            if keyword in upper_line:
                return upper_line.split(keyword)[0].strip()
    for line in lines:
        if line.isupper() and len(line.split()) >= 2:
            return line.strip()
    return "Firma adı düzgün okunamıyor"

# ----------------------------
# POS fiş parser (Visa, Mastercard, İş Bankası vs.)
# ----------------------------
def filter_ocr_pos_fis(text):
    lines = text.splitlines()
    firma = extract_firma_pos_fis_v2(lines)

    tarih_match = re.search(r'(\d{2}[\/\.-]\d{2}[\/\.-]\d{4})', text)
    tarih = tarih_match.group(1) if tarih_match else "Tarih düzgün okunamıyor"

    saat_match = re.search(r'(\d{2}:\d{2}:\d{2}|\d{2}:\d{2})', text)
    saat = saat_match.group(1) if saat_match else "Saat düzgün okunamıyor"

    tutar = "Toplam tutar düzgün okunamıyor"
    found_satis = False
    for line in lines:
        if "SATIŞ" in line.upper():
            found_satis = True
        elif found_satis and "TL" in line.upper():
            match = re.search(r'([\d]{1,3}(?:[.,]\d{3})*[.,]\d{2})', line)
            if match:
                tutar = match.group(1)
                try:
                    clean = tutar.replace(".", "").replace(",", ".")
                    if float(clean) < 1:
                        tutar = "Toplam tutar düzgün okunamıyor"
                except:
                    tutar = "Toplam tutar düzgün okunamıyor"
                break

    return {
        "firma": firma,
        "tarih": tarih,
        "saat": saat,
        "toplam_tutar": tutar
    }

def extract_firma_pos_fis_v2(lines):
    ignore_keywords = ['BANKASI', 'APP LABEL', 'VISA', 'MASTERCARD', 'PAYWAVE', 'ONAY KODU', 'SATIŞ']

    for i, line in enumerate(lines):
        if any(keyword in line.upper() for keyword in ["İŞYERİ", "ISYERI", "MERSİS", "TİC", "TİC."]):
            for j in range(i - 3, i):
                if j >= 0:
                    candidate = lines[j].strip().upper()
                    if (
                        5 < len(candidate) < 40 and
                        not any(kw in candidate for kw in ignore_keywords) and
                        any(c.isalpha() for c in candidate)
                    ):
                        return candidate.title()

    for line in lines:
        upper = line.strip().upper()
        if (
            5 < len(upper) < 40 and
            not any(kw in upper for kw in ignore_keywords) and
            upper.replace(" ", "").isalpha()
        ):
            return upper.title()

    return "Firma adı düzgün okunamıyor"

@app.route("/")
def home():
    return "OCR API çalışıyor. POST /upload ile fiş yükleyin."

if __name__ == "__main__":
    app.run(debug=True, port=5000)
