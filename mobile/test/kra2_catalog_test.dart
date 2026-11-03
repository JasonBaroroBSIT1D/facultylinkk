import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/kra2_catalog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    await Kra2Catalog.ensureLoaded();
  });

  test('loads 54 indicators', () {
    final all = [
      ...Kra2Catalog.indicatorsFor(Kra2Catalog.criterionA),
      ...Kra2Catalog.indicatorsFor(Kra2Catalog.criterionB),
      ...Kra2Catalog.indicatorsFor(Kra2Catalog.criterionC),
    ];
    expect(all.length, 54);
  });

  test('journal co-author requires contribution certificate', () {
    expect(
      Kra2Catalog.requiresContributionCertificate('kra2-a-journal-co'),
      isTrue,
    );
    expect(
      Kra2Catalog.requiresContributionCertificate('kra2-a-journal-sole'),
      isFalse,
    );
  });

  test('invention family metadata fields', () {
    final fields = Kra2Catalog.metadataFieldIds('kra2-b-patent-g');
    expect(fields, contains('registrationNumber'));
    expect(fields, contains('registrationDate'));
  });

  test('submission list hides raw upload filenames', () {
    final title = Kra2Catalog.submissionListTitle(
      indicatorId: 'kra2-b-patent-g-sole',
      outputTitle: 'KRA2_B_03_Patent_grant_certificate_Jason_Baroro',
    );
    expect(title, 'Patent certificate');
    expect(title.contains('KRA2_B'), isFalse);
  });

  test('detects grant certificate vs patent application mismatch', () {
    final hint = Kra2Catalog.documentTypeMismatchHint(
      'kra2-b-patent-a-sole',
      'KRA2_B_03_Patent_grant_certificate.pdf',
    );
    expect(hint, isNotNull);
    expect(hint!.toLowerCase(), contains('certificate'));
  });
}
