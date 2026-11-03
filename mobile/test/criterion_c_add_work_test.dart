import 'package:facultylink_app/data/criterion_c_catalog.dart';
import 'package:facultylink_app/navigation/app_routes.dart';
import 'package:facultylink_app/screens/criterion_c/criterion_c_add_work_screen.dart';
import 'package:facultylink_app/screens/documents/document_flow_args.dart';
import 'package:facultylink_app/theme/app_theme.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final captured = <FlutterErrorDetails>[];
  UploadDocumentLaunch? uploadLaunch;

  setUp(() {
    captured.clear();
    uploadLaunch = null;
    final prior = FlutterError.onError;
    FlutterError.onError = (details) {
      captured.add(details);
      prior?.call(details);
    };
  });

  tearDown(() {
    FlutterError.onError = FlutterError.presentError;
  });

  Future<void> pumpWizard(WidgetTester tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        initialRoute: '/',
        routes: {
          '/': (_) => const CriterionCAddWorkScreen(),
          AppRoutes.uploadDocument: (context) {
            final args = ModalRoute.of(context)?.settings.arguments;
            if (args is UploadDocumentLaunch) uploadLaunch = args;
            return const Scaffold(body: Text('Upload stub'));
          },
        },
      ),
    );
    await tester.pumpAndSettle();
    expect(captured, isEmpty, reason: _errors(captured));
  }

  testWidgets('research wizard has no estimated points step', (tester) async {
    await pumpWizard(tester);
    expect(find.text('Estimated points'), findsNothing);

    await tester.tap(find.text('Research advising / panel'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Estimated points'), findsNothing);
    expect(find.text('Research type'), findsOneWidget);

    final firstType = CriterionCCatalog.researchTypes.first.label;
    await tester.tap(find.text(firstType));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Estimated points'), findsNothing);
    expect(find.text('Your role'), findsOneWidget);

    await tester.tap(find.text('Adviser'));
    await tester.pumpAndSettle();
    expect(find.text('Upload approval sheet'), findsOneWidget);
    expect(find.text('Estimated points'), findsNothing);
  });

  testWidgets('research role step navigates to upload with OCR-first launch', (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.text('Research advising / panel'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(CriterionCCatalog.researchTypes.first.label));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Panel member'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Upload approval sheet'));
    await tester.pumpAndSettle();

    expect(find.text('Upload stub'), findsOneWidget);
    expect(uploadLaunch, isNotNull);
    expect(uploadLaunch!.criterionCPrimaryFlow, isTrue);
    expect(uploadLaunch!.criterionCOcrFirstResearch, isTrue);
    expect(uploadLaunch!.criterionId, CriterionCCatalog.criterionId);
    expect(uploadLaunch!.indicatorId, isNotEmpty);
  });

  testWidgets('research back navigation walks steps without gaps', (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.text('Research advising / panel'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(CriterionCCatalog.researchTypes.first.label));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Your role'), findsOneWidget);

    await tester.tap(find.text('Back'));
    await tester.pumpAndSettle();
    expect(find.text('Research type'), findsOneWidget);

    await tester.tap(find.text('Back'));
    await tester.pumpAndSettle();
    expect(find.text('What type of service?'), findsOneWidget);
  });

  testWidgets('mentorship wizard has no estimated points step', (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.text('Mentorship services'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('Estimated points'), findsNothing);
    expect(find.text('Mentorship details'), findsOneWidget);
  });

  testWidgets('mentorship details navigates to upload launch', (tester) async {
    await pumpWizard(tester);
    await tester.tap(find.text('Mentorship services'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();

    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'Robotics club');
    await tester.pumpAndSettle();
    await tester.enterText(fields.at(1), 'Regional fair');
    await tester.pumpAndSettle();

    await tester.tap(find.text('Upload documents'));
    await tester.pumpAndSettle();

    expect(find.text('Upload stub'), findsOneWidget);
    expect(uploadLaunch, isNotNull);
    expect(uploadLaunch!.criterionCPrimaryFlow, isTrue);
    expect(uploadLaunch!.criterionCOcrFirstResearch, isFalse);
    expect(uploadLaunch!.criterionCDraft?.isMentorship, isTrue);
    expect(uploadLaunch!.criterionCDraft?.projectTitle, 'Robotics club');
    expect(uploadLaunch!.criterionCDraft?.competitionName, 'Regional fair');
  });
}

String _errors(List<FlutterErrorDetails> details) {
  return details.map((d) => d.exceptionAsString()).join('\n');
}
