import 'dart:io';
import 'dart:typed_data';

import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

Future<String?> saveDocumentBytes(Uint8List bytes, String fileName) async {
  final dir = await getTemporaryDirectory();
  final safeName = fileName.replaceAll(RegExp(r'[^\w.\-]+'), '_');
  final file = File('${dir.path}/fl_$safeName');
  await file.writeAsBytes(bytes, flush: true);
  return file.path;
}

Future<bool> openSavedDocument(String path) async {
  final result = await OpenFilex.open(path);
  return result.type == ResultType.done;
}

Future<bool> openDocumentBytesInBrowser(
  Uint8List bytes, {
  required String fileName,
  String? mimeType,
}) async =>
    false;
