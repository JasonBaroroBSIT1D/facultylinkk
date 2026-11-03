bool isKra2JournalIndicator(String? indicatorId) {
  final id = (indicatorId ?? '').trim();
  return id == 'kra2-a-journal-sole' || id == 'kra2-a-journal-co';
}
