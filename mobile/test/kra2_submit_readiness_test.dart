import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_app/data/kra2_submit_readiness.dart';

void main() {
  test('can submit when controllers have title and slots present', () {
    final ready = Kra2SubmitReadiness.canSubmitForReview(
      fieldIds: ['outputTitle', 'authorsLine', 'outputVenue', 'publicationDate'],
      indicatorId: 'kra2-c-acting',
      requiredSlotIds: ['primary_output', 'role_certification'],
      controllerText: (id) => switch (id) {
        'outputTitle' => 'wowow',
        'authorsLine' => 'Jane Doe',
        'outputVenue' => 'CCP',
        'publicationDate' => '2025-01-01',
        _ => '',
      },
      slotMissing: (_) => false,
      bundle: const {'indicatorId': 'kra2-c-acting'},
    );
    expect(ready, isTrue);
  });

  test('cannot submit when title only in controller not bundle', () {
    final ready = Kra2SubmitReadiness.canSubmitForReview(
      fieldIds: ['outputTitle', 'authorsLine', 'outputVenue', 'publicationDate'],
      indicatorId: 'kra2-c-acting',
      requiredSlotIds: ['primary_output'],
      controllerText: (id) => id == 'outputTitle' ? 'wowow' : '',
      slotMissing: (_) => false,
      bundle: const {'indicatorId': 'kra2-c-acting'},
    );
    expect(ready, isFalse);
  });

  test('local blockers clear when title entered in controller', () {
    final blockers = Kra2SubmitReadiness.localBlockers(
      fieldIds: ['outputTitle', 'authorsLine', 'outputVenue', 'publicationDate'],
      indicatorId: 'kra2-c-acting',
      requiredSlotIds: ['primary_output'],
      controllerText: (id) => id == 'outputTitle' ? 'wowow' : '',
      fieldLabel: (id) => id,
      slotLabel: (_) => 'Primary evidence',
      slotMissing: (_) => false,
      bundle: const {'indicatorId': 'kra2-c-acting', 'outputTitle': ''},
    );
    expect(blockers.any((b) => b.contains('title')), isFalse);
    expect(blockers.any((b) => b.contains('performer') || b.contains('author')), isTrue);
  });

  test('instruction text does not count as author name', () {
    expect(
      Kra2SubmitReadiness.metadataComplete(
        fieldIds: ['authorsLine'],
        indicatorId: 'kra2-c-acting',
        controllerText: (_) => 'You can try reading again or enter the missing information below.',
        bundle: const {'indicatorId': 'kra2-c-acting'},
      ),
      isFalse,
    );
  });
}
