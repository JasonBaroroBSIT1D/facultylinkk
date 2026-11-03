import 'package:facultylink_app/data/criterion_c_bulk_upload.dart';
import 'package:facultylink_app/data/criterion_c_catalog.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('research assignable slots match backend checklist', () {
    expect(
      CriterionCBulkUpload.assignableSlots(mentorship: false),
      CriterionCCatalog.requiredSlots(mentorship: false),
    );
    expect(CriterionCBulkUpload.assignableSlots(mentorship: false), ['approval_sheet', 'rrpa_copc']);
  });

  test('mentorship assignable slots match backend checklist', () {
    expect(
      CriterionCBulkUpload.assignableSlots(mentorship: true),
      CriterionCCatalog.requiredSlots(mentorship: true),
    );
  });

  test('filename hints map approval and rrpa', () {
    final allowed = CriterionCBulkUpload.assignableSlots(mentorship: false);
    expect(
      CriterionCBulkUpload.suggestSlotFromFileName('Signed_Approval_Sheet.pdf', allowedSlots: allowed),
      CriterionCBulkUpload.approvalSheetSlot,
    );
    expect(
      CriterionCBulkUpload.suggestSlotFromFileName('RRPA_2024.pdf', allowedSlots: allowed),
      CriterionCBulkUpload.rrpaCopcSlot,
    );
  });

  test('research validation requires exactly one approval sheet', () {
    expect(
      CriterionCBulkUpload.validateAssignments(
        ['approval_sheet', 'rrpa_copc'],
        mentorship: false,
      ),
      isNull,
    );
    expect(
      CriterionCBulkUpload.validateAssignments(
        ['rrpa_copc', 'rrpa_copc'],
        mentorship: false,
      ),
      isNotNull,
    );
    expect(
      CriterionCBulkUpload.validateAssignments(
        [null, 'approval_sheet'],
        mentorship: false,
      ),
      isNotNull,
    );
  });
}
