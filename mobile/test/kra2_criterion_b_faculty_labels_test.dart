import 'package:facultylink_app/data/kra2_catalog.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('patent grant sole requires IPOPHL doc, photo, and special order', () {
    expect(
      Kra2Catalog.requiredEvidenceSlots('kra2-b-patent-g-sole'),
      ['primary_output', 'invention_photo', 'president_special_order'],
    );
  });

  test('commercialization local requires five evidence slots', () {
    final slots = Kra2Catalog.requiredEvidenceSlots('kra2-b-comm-local');
    expect(slots.length, 5);
    expect(slots, contains('commercialization_proof'));
  });

  test('slot labels use faculty-friendly patent wording', () {
    expect(
      Kra2Catalog.slotLabelForIndicator('primary_output', 'kra2-b-patent-a-sole'),
      'IPOPHL patent stage document',
    );
  });

  test('co-developer software includes sole checklist plus contribution', () {
    final sole = Kra2Catalog.requiredEvidenceSlots('kra2-b-sw-new-sole');
    final co = Kra2Catalog.requiredEvidenceSlots('kra2-b-sw-new-co');
    expect(co.length, sole.length + 1);
    expect(co.last, 'contribution_certificate');
    expect(co.sublist(0, sole.length), sole);
  });

  test('co-developer variety uses deposit and annex H only', () {
    expect(
      Kra2Catalog.requiredEvidenceSlots('kra2-b-variety-co'),
      ['registration_deposit_evidence', 'contribution_certificate'],
    );
  });
}
