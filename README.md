# 🧾 OCR Receipt Scanning API
This project is a Flask-based OCR (Optical Character Recognition) API designed to extract structured data such as company name, date, time, and total amount from receipt images. It supports multiple receipt formats including classic printed receipts, e-archive invoices, and POS machine outputs.

## ✨ Features
## 📷 Text extraction from receipt images using pytesseract

## 🧠 Automatic format detection: classic, e-archive, and POS receipts

## 🧾 Accurate parsing of key fields: company name, date, time, and total amount

## 🔍 Format-specific parsing logic with regex-based field matching

## 📤 Multi-file upload support via /upload endpoint

## 🧩 Preprocessing pipeline for denoising, sharpening, and contrast enhancement

## 📦 JSON output with clear error messages for unreadable fields

## 🔄 Designed to integrate with mobile apps and web clients

🛠️ Technologies Used
Python 3

Flask (for the API)

Pillow (image processing)

PyTesseract(image preprocessing)

PyTesseract (OCR engine)

Regex (for parsing logic)

## 📦 Installation

# Clone the repository
git clone https://github.com/cancrpcoglu/ocr-reciept-scanning.git
cd ocr-reciept-scanning

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Make sure Tesseract is installed
# Example for Windows:
# Download from https://github.com/tesseract-ocr/tesseract and set the path below

## 📤 API Endpoint
POST /upload
Upload one or more receipt images and receive structured data.

Request (multipart/form-data)

Key: image
Value: (select image file or multiple)

Response (JSON)
{
  "ocr_results": [
    {
      "filename": "receipt1.jpg",
      "ocr_text": "...raw text...",
      "parsed": {
        "firma": "XYZ MARKET",
        "tarih": "03.08.2025",
        "saat": "15:42:10",
        "toplam_tutar": "87.50"
      }
    },
    ...
  ]
}

## 📁 Supported Formats
Classic printed receipts

E-Archive invoices

POS device receipts (e.g., İş Bankası, Visa, Mastercard)

Each format is detected and parsed with its own logic to ensure high accuracy.

To improve OCR accuracy, each image goes through preprocessing:

Grayscale conversion

Contrast enhancement

Sharpening

Resizing

Noise removal using PyTesseract

## 🧠 Error Handling
If any field (e.g., company name or date) cannot be correctly extracted, it will return a descriptive fallback like:
"firma": "Company name could not be read"

📱 Integration Example
This API was successfully integrated into a Flutter mobile application, using http.MultipartRequest for image upload and JSON parsing for OCR results.

## ✍️ Author
Can Çorapçıoğlu 
[GitHub](https://github.com/cancrpcoglu) | [LinkedIn](https://www.linkedin.com/in/can-%C3%A7orap%C3%A7%C4%B1o%C4%9Flu-15a340247/)
