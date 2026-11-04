import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_app/data/kra2_a_ux.dart';

void main() {
  test('faculty status mapping', () {
    expect(
      Kra2AUx.facultyStatus(reviewStatus: 'approved', validationStatus: 'valid', submittedForReview: true),
      Kra2FacultyStatus.approved,
    );
    expect(
      Kra2AUx.facultyStatus(reviewStatus: 'pending', validationStatus: 'incomplete', submittedForReview: true),
      Kra2FacultyStatus.underReview,
    );
    expect(
      Kra2AUx.facultyStatus(reviewStatus: 'pending', validationStatus: 'incomplete', submittedForReview: false),
      Kra2FacultyStatus.draft,
    );
    expect(
      Kra2AUx.facultyStatus(reviewStatus: 'rejected', validationStatus: 'invalid', submittedForReview: true),
      Kra2FacultyStatus.needsChanges,
    );
  });

  test('humanize blockers', () {
    expect(
      Kra2AUx.humanizeBlocker('Title of the research output is required.'),
      'Please enter the title.',
    );
    expect(
      Kra2AUx.humanizeBlocker(
        'Please enter the author or inventor names.',
        indicatorId: 'kra2-a-journal-sole',
      ),
      'Please check the author names.',
    );
    expect(
      Kra2AUx.humanizeBlocker(
        'Please enter the author or inventor names.',
        indicatorId: 'kra2-b-patent-a-sole',
      ),
      'Please check the inventor names.',
    );
  });
}
