import 'package:facultylink_app/data/criterion_b_bulk_upload.dart';
import 'package:facultylink_app/screens/documents/document_flow_args.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('co-author textbook includes annex c slot', () {
    final slots = CriterionBBulkUpload.assignableSlots(
      draft: const CriterionBAddWorkDraft(
        accomplishmentKind: 'instructional_material',
        indicatorId: 'kra1-b-textbook-co',
        materialTitle: 'Intro',
        materialType: 'textbook',
        contributionPercent: 40,
      ),
      indicatorId: 'kra1-b-textbook-co',
    );
    expect(slots, contains('annex_c_contribution'));
    expect(slots, contains('primary_material'));
  });

  test('filename hints map to slots when clear', () {
    final allowed = CriterionBBulkUpload.assignableSlots(
      draft: const CriterionBAddWorkDraft(
        accomplishmentKind: 'instructional_material',
        indicatorId: 'kra1-b-textbook-sole',
        materialTitle: 'T',
        materialType: 'textbook',
      ),
      indicatorId: 'kra1-b-textbook-sole',
    );
    expect(
      CriterionBBulkUpload.suggestSlotFromFileName(
        '03_Approved_Course_Syllabus.pdf',
        allowedSlots: allowed,
      ),
      'approved_syllabus',
    );
    expect(
      CriterionBBulkUpload.suggestSlotFromFileName(
        '04_Library_Certification.pdf',
        allowedSlots: allowed,
      ),
      'library_certification',
    );
  });

  test('validation requires one primary', () {
    expect(
      CriterionBBulkUpload.validateAssignments(
        ['approved_syllabus', 'library_certification'],
        program: false,
      ),
      isNotNull,
    );
    expect(
      CriterionBBulkUpload.validateAssignments(
        ['primary_material', 'approved_syllabus'],
        program: false,
      ),
      isNull,
    );
  });
}
