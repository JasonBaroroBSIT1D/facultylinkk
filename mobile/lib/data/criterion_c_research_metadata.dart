/// Research metadata display helpers (mirror backend unreliable-title rules).
abstract final class CriterionCResearchMetadata {
  static bool isUnreliableTitle(String? value) {
    final text = (value ?? '').trim();
    if (text.isEmpty || text.length < 4) return true;
    final lower = text.toLowerCase();
    if (lower.contains('signed approval sheet') || lower.contains('approval sheet')) return true;
    if (lower.contains('sample')) return true;
    if (RegExp(r'^\d{1,3}[\s._-]+(?:signed|approval|sheet)', caseSensitive: false).hasMatch(text)) {
      return true;
    }
    if (RegExp(r'\.(pdf|docx?|png|jpe?g)\b', caseSensitive: false).hasMatch(text)) return true;
    if (text.split('_').length >= 3 && text.split(' ').length <= 2) return true;
    return false;
  }

  static String effectiveFieldValue({
    required String key,
    required String bundleValue,
    required Map<String, dynamic>? ocrFields,
    required Map<String, dynamic>? metadataConfirmed,
  }) {
    var value = bundleValue.trim();
    final confirmed = metadataConfirmed?[key] == true;
    if (key == 'projectTitle' && isUnreliableTitle(value)) {
      value = '';
    }
    if (value.isEmpty && ocrFields != null) {
      final entry = ocrFields[key];
      if (entry is Map) {
        final ocrVal = (entry['value'] ?? '').toString().trim();
        if (key != 'projectTitle' || !isUnreliableTitle(ocrVal)) {
          value = ocrVal;
        }
      }
    }
    if (confirmed) {
      final fromBundle = bundleValue.trim();
      if (fromBundle.isNotEmpty) return fromBundle;
    }
    return value;
  }

  static bool metadataFullyConfirmed(Map<String, dynamic>? bundle) {
    if (bundle == null) return false;
    final confirmed = bundle['metadataConfirmed'];
    if (confirmed is! Map) return false;
    return confirmed['projectTitle'] == true &&
        confirmed['studentNames'] == true &&
        confirmed['completionDate'] == true;
  }
}
