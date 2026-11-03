import 'package:flutter_test/flutter_test.dart';
import 'package:facultylink_app/data/kra2_a_evidence.dart';

void main() {
  test('journal indicator detection', () {
    expect(isKra2JournalIndicator('kra2-a-journal-sole'), isTrue);
    expect(isKra2JournalIndicator('kra2-a-journal-co'), isTrue);
    expect(isKra2JournalIndicator('kra2-a-book-sole'), isFalse);
  });
}
