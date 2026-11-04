import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_app/data/kra2_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    await Kra2Catalog.ensureLoaded();
  });

  test('Criterion C has 25 indicators', () {
    expect(Kra2Catalog.indicatorsFor(Kra2Catalog.criterionC).length, 25);
  });

  test('metadata and slots for every C indicator', () {
    for (final row in Kra2Catalog.indicatorsFor(Kra2Catalog.criterionC)) {
      final id = row['id']!.toString();
      final sub = Kra2Catalog.criterionCSubfamily(id);
      expect(sub, isNotEmpty);
      for (final field in ['outputTitle', 'authorsLine', 'outputVenue', 'publicationDate']) {
        final label = Kra2Catalog.metadataLabelForIndicator(field, id);
        expect(label, isNot(isEmpty));
        expect(label.toLowerCase(), isNot(contains('journal')));
        expect(label.toLowerCase(), isNot(contains('doi')));
      }
      final fields = Kra2Catalog.metadataFieldIds(id);
      expect(fields, contains('outputTitle'));
      expect(fields, isNot(contains('publicationReference')));
      final slots = Kra2Catalog.requiredEvidenceSlots(id);
      expect(slots, isNotEmpty);
      expect(slots.first, 'primary_output');
    }
  });
}
