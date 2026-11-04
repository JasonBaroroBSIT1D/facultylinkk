import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_app/data/kra3_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    await Kra3Catalog.preload();
  });

  test('loads 46 KRA III indicators', () {
    expect(Kra3Catalog.indicatorsFor(Kra3Catalog.criterionA).length, 11);
    expect(Kra3Catalog.indicatorsFor(Kra3Catalog.criterionB).length, 14);
    expect(Kra3Catalog.indicatorsFor(Kra3Catalog.criterionC).length, 1);
    expect(Kra3Catalog.indicatorsFor(Kra3Catalog.criterionD).length, 20);
  });

  test('accomplishment groups cover every indicator id', () {
    for (final cid in [
      Kra3Catalog.criterionA,
      Kra3Catalog.criterionB,
      Kra3Catalog.criterionC,
      Kra3Catalog.criterionD,
    ]) {
      final groups = Kra3Catalog.accomplishmentGroups(cid);
      final ids = groups.expand((g) => g.indicatorIds).toSet();
      final catalogIds = Kra3Catalog.indicatorsFor(cid).map((r) => r['id'] as String).toSet();
      expect(ids, catalogIds, reason: cid);
    }
  });
}
