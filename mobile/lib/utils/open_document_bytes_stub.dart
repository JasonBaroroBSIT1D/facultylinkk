import 'dart:typed_data';

Future<String?> saveDocumentBytes(Uint8List bytes, String fileName) async {
  throw UnsupportedError('Opening local files is not supported on this platform.');
}

Future<bool> openSavedDocument(String path) async => false;

Future<bool> openDocumentBytesInBrowser(
  Uint8List bytes, {
  required String fileName,
  String? mimeType,
}) async =>
    false;
