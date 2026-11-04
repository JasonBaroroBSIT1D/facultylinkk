import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_app/data/kra2_catalog.dart';

void main() {
  test('acting performance uses performance workflow family', () {
    expect(Kra2Catalog.workflowFamily('kra2-c-acting'), 'performance_work');
  });

  test('acting metadata labels are performance-specific', () {
    expect(
      Kra2Catalog.metadataLabelForIndicator('outputTitle', 'kra2-c-acting'),
      'Title of performance',
    );
    expect(
      Kra2Catalog.metadataLabelForIndicator('authorsLine', 'kra2-c-acting'),
      'Performer or director',
    );
    expect(
      Kra2Catalog.metadataLabelForIndicator('outputVenue', 'kra2-c-acting'),
      'Performance venue or organizer',
    );
    expect(
      Kra2Catalog.metadataLabelForIndicator('publicationDate', 'kra2-c-acting'),
      'Date of performance',
    );
  });

  test('acting required evidence slots match backend annex checklist', () {
    expect(
      Kra2Catalog.requiredEvidenceSlots('kra2-c-acting'),
      [
        'primary_output',
        'program_documentation',
        'media_documentation',
        'role_certification',
      ],
    );
  });

  test('acting metadata fields exclude patent registration', () {
    final fields = Kra2Catalog.metadataFieldIds('kra2-c-acting');
    expect(fields, contains('outputTitle'));
    expect(fields, isNot(contains('registrationNumber')));
    expect(fields, isNot(contains('publicationReference')));
  });
}
