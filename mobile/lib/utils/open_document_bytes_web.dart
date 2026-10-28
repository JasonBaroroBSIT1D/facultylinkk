import 'dart:async';
import 'dart:js_interop';
import 'dart:typed_data';

import 'package:web/web.dart';

Future<String?> saveDocumentBytes(Uint8List bytes, String fileName) async {
  // Web has no durable temp path; bytes stay in memory and open via blob URL.
  return null;
}

Future<bool> openSavedDocument(String path) async => false;

Future<bool> openDocumentBytesInBrowser(
  Uint8List bytes, {
  required String fileName,
  String? mimeType,
}) async {
  final mime = (mimeType ?? '').trim().isEmpty
      ? _guessMime(fileName)
      : mimeType!;
  final blob = Blob(
    <BlobPart>[bytes.toJS].toJS,
    BlobPropertyBag(type: mime),
  );
  final url = URL.createObjectURL(blob);
  window.open(url, '_blank');
  unawaited(
    Future<void>.delayed(const Duration(seconds: 60), () {
      URL.revokeObjectURL(url);
    }),
  );
  return true;
}

String _guessMime(String fileName) {
  final lower = fileName.toLowerCase();
  if (lower.endsWith('.pdf')) return 'application/pdf';
  if (lower.endsWith('.png')) return 'image/png';
  if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return 'image/jpeg';
  if (lower.endsWith('.webp')) return 'image/webp';
  if (lower.endsWith('.gif')) return 'image/gif';
  if (lower.endsWith('.doc')) return 'application/msword';
  if (lower.endsWith('.docx')) {
    return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
  }
  return 'application/octet-stream';
}
