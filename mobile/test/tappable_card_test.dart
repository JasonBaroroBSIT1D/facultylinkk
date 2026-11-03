import 'package:facultylink_app/widgets/tappable_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('TappableCard invokes onTap after frame', (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: TappableCard(
            onTap: () => tapped = true,
            child: const Text('Tap me'),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Tap me'));
    expect(tapped, isFalse);
    await tester.pump();
    expect(tapped, isTrue);
  });
}
