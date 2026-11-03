/// Plain-language options for KRA II Criterion A journal articles.
abstract final class Kra2AJournalCatalog {
  static const criterionId = 'kra2-a';

  static const soleIndicatorId = 'kra2-a-journal-sole';
  static const coIndicatorId = 'kra2-a-journal-co';

  static const journalTypes = <JournalArticleType>[
    JournalArticleType(
      indicatorId: soleIndicatorId,
      title: 'I am the only author',
      summary:
          'You wrote the entire article yourself. Upload a copy of the published article showing your name, the journal, and the date.',
      requiresContributionForm: false,
    ),
    JournalArticleType(
      indicatorId: coIndicatorId,
      title: 'I wrote it with co-authors',
      summary:
          'You share credit with other authors. Upload the published article and your signed Certificate of Contribution (Annex D) showing your percentage.',
      requiresContributionForm: true,
    ),
  ];

  static JournalArticleType? typeForIndicator(String? indicatorId) {
    final id = (indicatorId ?? '').trim();
    for (final t in journalTypes) {
      if (t.indicatorId == id) return t;
    }
    return null;
  }

  static String slotLabel(String slotId) {
    switch (slotId) {
      case 'primary_output':
        return 'Published journal article (PDF)';
      case 'contribution_certificate':
        return 'Certificate of Contribution (Annex D)';
      default:
        return slotId.replaceAll('_', ' ');
    }
  }
}

class JournalArticleType {
  const JournalArticleType({
    required this.indicatorId,
    required this.title,
    required this.summary,
    required this.requiresContributionForm,
  });

  final String indicatorId;
  final String title;
  final String summary;
  final bool requiresContributionForm;
}
