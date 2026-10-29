import 'package:http_parser/http_parser.dart';

/// MIME type for multipart uploads when the platform omits Content-Type.
MediaType? mediaTypeForUploadFileName(String fileName) {
  final dot = fileName.lastIndexOf('.');
  if (dot < 0 || dot == fileName.length - 1) return null;
  switch (fileName.substring(dot + 1).toLowerCase()) {
    case 'pdf':
      return MediaType('application', 'pdf');
    case 'jpg':
    case 'jpeg':
      return MediaType('image', 'jpeg');
    case 'png':
      return MediaType('image', 'png');
    case 'webp':
      return MediaType('image', 'webp');
    case 'gif':
      return MediaType('image', 'gif');
    default:
      return null;
  }
}
