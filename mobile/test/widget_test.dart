import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/app_state.dart';
import 'package:facultylink_app/main.dart';
import 'package:facultylink_app/navigation/main_shell.dart';
import 'package:facultylink_app/theme/app_theme.dart';

void main() {
  setUpAll(AppState.instance.prepareForWidgetTests);

  Future<void> setPhoneSize(WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
  }

  testWidgets('splash has no buttons and opens login after 3 seconds', (tester) async {
    await setPhoneSize(tester);
    await tester.pumpWidget(const FacultyLinkApp());

    expect(find.text('Prepare Your\nRank Upgrade here'), findsOneWidget);
    expect(find.text('Self Assessment'), findsWidgets);
    expect(find.text('Login'), findsNothing);
    expect(find.text('Register'), findsNothing);
    expect(find.byType(FilledButton), findsNothing);

    await tester.pump(const Duration(milliseconds: 2900));
    expect(find.text('Login here'), findsNothing);

    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();

    expect(find.text('Login here'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.text('Forgot your password?'), findsOneWidget);
    expect(find.text('Create new account'), findsNothing);
    expect(find.text('Or continue with'), findsNothing);
    expect(find.text('G'), findsNothing);
    expect(find.byIcon(Icons.facebook), findsNothing);
    expect(find.byIcon(Icons.apple), findsNothing);

    final navigator = tester.state<NavigatorState>(find.byType(Navigator));
    expect(navigator.canPop(), isFalse);
  });

  testWidgets('reduced motion shows the splash fully and still reaches login', (tester) async {
    await setPhoneSize(tester);
    tester.platformDispatcher.accessibilityFeaturesTestValue =
        const FakeAccessibilityFeatures(disableAnimations: true);
    addTearDown(tester.platformDispatcher.clearAccessibilityFeaturesTestValue);

    await tester.pumpWidget(const FacultyLinkApp());
    final heading = tester.widget<FadeTransition>(
      find.ancestor(
        of: find.text('Prepare Your\nRank Upgrade here'),
        matching: find.byType(FadeTransition),
      ).first,
    );
    expect(heading.opacity.value, 1.0);

    await tester.pump(const Duration(milliseconds: 2700));
    await tester.pumpAndSettle();
    expect(find.text('Login here'), findsOneWidget);
  });

  testWidgets('login scrolls with the keyboard open on a small screen', (tester) async {
    await tester.binding.setSurfaceSize(const Size(320, 568));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    tester.view.viewInsets = const FakeViewPadding(bottom: 600);
    addTearDown(tester.view.resetViewInsets);

    await tester.pumpWidget(const FacultyLinkApp());
    await tester.pump(const Duration(seconds: 4));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    await tester.drag(find.byType(SingleChildScrollView), const Offset(0, -400));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.text('Sign in'), findsOneWidget);
    expect(tester.getRect(find.text('Sign in')).bottom, lessThanOrEqualTo(568));
  });

  testWidgets('login validates fields and toggles password visibility', (tester) async {
    await setPhoneSize(tester);
    await tester.pumpWidget(const FacultyLinkApp());
    await tester.pump(const Duration(seconds: 4));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Sign in'));
    await tester.pumpAndSettle();
    expect(find.text('Enter your faculty email'), findsOneWidget);
    expect(find.text('Enter your password'), findsOneWidget);

    EditableText passwordField() => tester.widget<EditableText>(
          find.descendant(
            of: find.widgetWithText(TextFormField, 'Password'),
            matching: find.byType(EditableText),
          ),
        );
    expect(passwordField().obscureText, isTrue);
    await tester.tap(find.byIcon(Icons.visibility_outlined));
    await tester.pump();
    expect(passwordField().obscureText, isFalse);
  });

  testWidgets('forgot password: email, OTP, new password, back to login', (tester) async {
    await setPhoneSize(tester);
    AppState.instance.resetAuthForTests();
    addTearDown(AppState.instance.resetAuthForTests);

    await tester.pumpWidget(const FacultyLinkApp());
    await tester.pump(const Duration(seconds: 4));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Forgot your password?'));
    await tester.pumpAndSettle();
    expect(find.text('Forgot password'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField), 'nope');
    await tester.tap(find.text('Send code'));
    await tester.pumpAndSettle();
    expect(find.text('Enter a valid email address'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField), 'maria.santos@university.edu.ph');
    await tester.tap(find.text('Send code'));
    await tester.pumpAndSettle();
    expect(find.text('Enter code'), findsOneWidget);
    expect(find.text('Resend code in 60s'), findsOneWidget);
    expect(find.textContaining('Code expires in 05:00'), findsOneWidget);

    await tester.tap(find.text('Resend code in 60s'));
    await tester.pumpAndSettle();

    await tester.pump(const Duration(seconds: 61));
    expect(find.text('Resend code'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField), '000000');
    await tester.tap(find.text('Verify'));
    await tester.pumpAndSettle();
    expect(find.text('Enter code'), findsOneWidget);
    expect(find.text('The code is invalid or has expired. Request a new code.'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField), '123456');
    await tester.tap(find.text('Verify'));
    await tester.pumpAndSettle();
    expect(find.text('Code verified. Choose a new password\nfor your account.'), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextFormField, 'New password'), 'NewSecret456');
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Confirm new password'),
      'Different999',
    );
    await tester.tap(find.text('Update password'));
    await tester.pumpAndSettle();
    expect(find.text('Passwords do not match'), findsOneWidget);

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Confirm new password'),
      'NewSecret456',
    );
    await tester.tap(find.text('Update password'));
    await tester.pumpAndSettle();
    expect(find.text('Password updated'), findsOneWidget);

    await tester.tap(find.text('Go to sign in'));
    await tester.pumpAndSettle();
    expect(find.text('Login here'), findsOneWidget);
    expect(find.text('maria.santos@university.edu.ph'), findsOneWidget);
  });

  testWidgets('faculty shell tabs show mock faculty data', (WidgetTester tester) async {
    await setPhoneSize(tester);
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: const MainShell(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('Maria Santos'), findsWidgets);
    expect(find.text('Simulation Result'), findsOneWidget);
    expect(find.text('Eligible For'), findsOneWidget);
    expect(find.text('Readiness'), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Preparation period'), findsOneWidget);
    expect(find.text('Closing Soon'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.description_outlined));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 800));
    expect(find.text('Add document'), findsOneWidget);
    expect(find.text('Preparation period'), findsWidgets);
    expect(find.text('Closing Soon'), findsWidgets);

    await tester.tap(find.byIcon(Icons.track_changes_outlined));
    await tester.pumpAndSettle();
    expect(find.text('Instructor I'), findsWidgets);
    expect(find.text('Instructor II'), findsWidgets);
    expect(find.text('Simulation Result'), findsWidgets);
    expect(find.text('Readiness'), findsWidgets);

    await tester.tap(
      find.descendant(
        of: find.byType(NavigationBar),
        matching: find.text('Notifications'),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Notifications'), findsWidgets);

    await tester.tap(find.text('Profile').hitTestable());
    await tester.pumpAndSettle();
    expect(find.text('FL-2024-0847'), findsOneWidget);
    await tester.fling(find.text('FL-2024-0847'), const Offset(0, -500), 1200);
    await tester.pumpAndSettle();
    expect(find.text('Edit profile'), findsOneWidget);
  });
}
