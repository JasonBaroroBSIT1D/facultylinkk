import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/kra2_a_ux.dart';
import 'package:facultylink_app/data/kra2_catalog.dart';
import 'package:facultylink_app/data/kra2_ocr_sync.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    await Kra2Catalog.ensureLoaded();
  });

  test('book sole author field labels', () {
    const id = 'kra2-a-book-sole';
    expect(Kra2Catalog.metadataLabelForIndicator('outputTitle', id), 'Title of your book');
    expect(Kra2Catalog.metadataLabelForIndicator('outputVenue', id), 'Publisher');
    expect(
      Kra2Catalog.metadataLabelForIndicator('publicationReference', id),
      'ISBN or reference number (optional)',
    );
  });

  test('journal sole keeps journal and DOI labels', () {
    const id = 'kra2-a-journal-sole';
    expect(Kra2Catalog.metadataLabelForIndicator('outputVenue', id), 'Journal name');
    expect(Kra2Catalog.metadataLabelForIndicator('publicationReference', id), 'DOI (if you have one)');
  });

  test('book sole evidence checklist includes peer review', () {
    expect(
      Kra2Catalog.requiredEvidenceSlots('kra2-a-book-sole'),
      ['primary_output', 'peer_review_evidence'],
    );
    expect(
      Kra2Catalog.slotLabelForIndicator('peer_review_evidence', 'kra2-a-book-sole'),
      'Peer review and academic press evidence',
    );
  });

  test('humanize blocker preserves missing document name', () {
    final msg = Kra2AUx.humanizeBlocker(
      'Please upload: Peer review and reputable academic press evidence.',
      indicatorId: 'kra2-a-book-sole',
    );
    expect(msg, contains('Peer review'));
    expect(msg, isNot('Please add the required document.'));
  });

  test('fictional test publisher is not treated as disclaimer label', () {
    const publisher = 'University Learning Press (FICTIONAL)';
    expect(Kra2OcrSync.isMetadataLabelValue(publisher, fieldId: 'outputVenue'), isFalse);
    expect(Kra2OcrSync.isDisclaimerTitle(publisher), isFalse);
  });

  test('all criterion A indicators have evidence slots', () {
    for (final row in Kra2Catalog.indicatorsFor(Kra2Catalog.criterionA)) {
      final id = row['id']?.toString() ?? '';
      expect(Kra2Catalog.requiredEvidenceSlots(id), isNotEmpty);
      expect(Kra2Catalog.requiredEvidenceSlots(id), contains('primary_output'));
    }
  });
}
