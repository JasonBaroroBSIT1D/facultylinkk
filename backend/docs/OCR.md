# FacultyLink OCR (Tesseract)

FacultyLink extracts text from uploaded PDF and image evidence using **Tesseract OCR** and **PyMuPDF** (PDF text / page rendering). OCR supports reviewer inspection only; it does **not** change KRA scoring or `verified_points`.

## Windows (development)

1. Install [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki) (add to PATH **or** set `TESSERACT_CMD`).
2. Verify: `tesseract --version`
3. In `backend/.env`:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
OCR_INLINE_AFTER_UPLOAD=true
```

4. Install Python deps: `pip install -r requirements.txt`
5. Verify API: `GET /api/health` → `"ocr": { "available": true, ... }`

## Ubuntu / Linux (deployment)

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
pip install -r requirements.txt
```

Leave `TESSERACT_CMD` unset to use `/usr/bin/tesseract`.

## Processing model

1. Upload → `documents.ocr_status = pending` + row in `document_ocr_jobs`.
2. Worker processes jobs → `processing` → `completed` or `failed`.
3. Results: `documents.extracted_text`, `ocr_confidence`, `extracted_info` (excerpt, quality, errors).

### Workers

- **Development:** `OCR_INLINE_AFTER_UPLOAD=true` runs a short background batch after each upload (Flask debug reloader safe).
- **Production:** run a dedicated worker:

```bash
flask --app app ocr-worker
```

One-shot: `flask --app app ocr-worker --once`

Re-queue old uploads: `flask --app app ocr-enqueue-stale`

## Limits (environment)

| Variable | Default | Purpose |
|----------|---------|---------|
| `OCR_MAX_PDF_PAGES` | 50 | Max PDF pages processed |
| `OCR_PDF_DPI` | 200 | Render DPI for scanned pages |
| `OCR_PAGE_TEXT_MIN_CHARS` | 40 | Min chars to treat a PDF page as text-based |
| `OCR_TIMEOUT_SECONDS` | 120 | Documented limit (future hook) |
| `OCR_MAX_ATTEMPTS` | 3 | Job retries |
| `OCR_STALE_PROCESSING_MINUTES` | 20 | Requeue stuck `processing` jobs |

## Confidence

Mean of Tesseract per-word confidences from `image_to_data` where `conf > 0`. If no valid words, confidence is `null` (text may still come from `image_to_string` or PDF text extraction).

## Supported uploads

Same as upload API: PDF, JPEG, PNG, WebP, GIF (first frame only for animated GIF).

## API

- Document payloads include `ocr.status`, `ocr.confidence`, `ocr.content` (detail views).
- Retry: `POST .../ocr/retry` (faculty owner, assigned reviewer, or administrator).
