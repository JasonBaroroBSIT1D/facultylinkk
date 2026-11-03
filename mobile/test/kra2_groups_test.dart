import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/kra2_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    await Kra2Catalog.ensureLoaded();
  });

  test('accomplishment groups cover all 54 indicators', () {
    final grouped = <String>{
      for (final g in Kra2Catalog.accomplishmentGroups(Kra2Catalog.criterionA))
        ...g.indicatorIds,
      for (final g in Kra2Catalog.accomplishmentGroups(Kra2Catalog.criterionB))
        ...g.indicatorIds,
      for (final g in Kra2Catalog.accomplishmentGroups(Kra2Catalog.criterionC))
        ...g.indicatorIds,
    };
    expect(grouped.length, 54);
  });

  test('journal group offers sole and co indicators', () {
    final groups = Kra2Catalog.accomplishmentGroups(Kra2Catalog.criterionA);
    final journal = groups.firstWhere((g) => g.key == 'journal');
    expect(journal.needsAuthorshipChoice, isTrue);
    expect(journal.soleIndicatorId, 'kra2-a-journal-sole');
    expect(journal.coIndicatorId, 'kra2-a-journal-co');
  });

  test('citation indicator stays under criterion A', () {
    final groups = Kra2Catalog.accomplishmentGroups(Kra2Catalog.criterionA);
    expect(groups.any((g) => g.key == 'cite'), isTrue);
    final cite = groups.firstWhere((g) => g.key == 'cite');
    expect(cite.indicatorIds, contains('kra2-a-cite'));
  });
}
