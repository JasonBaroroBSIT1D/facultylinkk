String titleFromFilename(String fileName) {
  var name = fileName.trim();
  if (name.isEmpty) return '';
  final slash = name.replaceAll('\\', '/').split('/').last;
  name = slash;
  final dot = name.lastIndexOf('.');
  if (dot > 0) {
    name = name.substring(0, dot);
  }
  name = name.replaceAll(RegExp(r'[_\-]+'), ' ');
  name = name.replaceAll(RegExp(r'\s+'), ' ').trim();
  if (name.isEmpty) return fileName;
  return name
      .split(' ')
      .map((part) {
        if (part.isEmpty) return part;
        if (RegExp(r'^\d+$').hasMatch(part)) return part;
        return part[0].toUpperCase() + part.substring(1);
      })
      .join(' ');
}
