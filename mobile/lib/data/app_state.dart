import 'dart:async';
import 'package:flutter/foundation.dart';

import '../models/enums.dart';
import '../models/models.dart';
import 'api_client.dart';
import 'app_auth_exception.dart';
import 'auth_response.dart';
import 'faculty_api_mapper.dart';
import 'faculty_session_defaults.dart';
import 'mock_auth.dart';
import 'mock_data.dart';

/// App-wide faculty state backed by Flask JWT APIs when signed in.
class AppState extends ChangeNotifier {
  AppState._()
      : faculty = FacultySessionDefaults.faculty,
        documents = const [],
        notifications = const [];

  static final AppState instance = AppState._();

  FacultyProfile faculty;
  List<FacultyDocument> documents;
  List<AppNotification> notifications;

  final Map<String, Uint8List> localDocumentBytes = {};

  DashboardSnapshot? _dashboard;
  List<KraScore>? _kraScores;
  RankSimulation? _simulation;
  List<RequirementItem>? _requirements;
  PreparationPeriod? _preparationPeriod;

  bool isSignedIn = false;
  bool mustChangePassword = false;
  bool refreshInProgress = false;
  String? busyMessage;
  DateTime? _lastRefreshAt;
  AssignedReviewer? assignedReviewer;
  bool assignedReviewerLoading = false;
  String? assignedReviewerError;
  bool _operationLocked = false;
  String _activePassword = MockAuth.demoPassword;
  String? _pendingResetToken;
  final ApiClient _api = ApiClient();
  bool _useMockAuthForTests = false;
  bool _sessionRestoreEnabled = true;

  bool get usesMockAuth => _useMockAuthForTests;
  bool get sessionRestoreEnabled => _sessionRestoreEnabled;
  String? signedInEmail;
  String? signedInUserId;

  int mainTabIndex = 0;
  int assessmentTabIndex = 0;

  DashboardSnapshot get dashboard {
    if (_useMockAuthForTests) return _dashboard ?? MockData.dashboard;
    if (!isSignedIn) return FacultySessionDefaults.dashboard;
    return _dashboard ?? FacultySessionDefaults.dashboard;
  }

  List<KraScore> get kraScores {
    if (_useMockAuthForTests) return _kraScores ?? MockData.kraScores;
    if (_kraScores != null) return _kraScores!;
    return dashboard.kraScores;
  }

  RankSimulation get simulation {
    if (_useMockAuthForTests) return _simulation ?? MockData.simulation;
    return _simulation ?? dashboard.simulation;
  }

  List<RequirementItem> get requirements {
    if (_useMockAuthForTests) return _requirements ?? MockData.requirements;
    return _requirements ?? const [];
  }

  PreparationPeriod get preparationPeriod {
    if (_useMockAuthForTests) {
      return _preparationPeriod ?? MockData.preparationPeriod;
    }
    return _preparationPeriod ?? FacultySessionDefaults.preparationPeriod;
  }

  Map<String, dynamic>? get criterionA =>
      _useMockAuthForTests ? MockData.criterionASample : null;

  bool get profileLoaded => _profileLoaded;
  bool _profileLoaded = false;

  int get unreadNotificationCount => notifications
      .where((n) => n.visualState != NotificationVisualState.read)
      .length;

  int get validatedCount =>
      documents.where((d) => d.status == DocumentStatus.validated).length;

  int get pendingCount =>
      documents.where((d) => d.status == DocumentStatus.pendingReview).length;

  int get actionRequiredCount => documents
      .where((d) =>
          d.status == DocumentStatus.needsRevision ||
          d.status == DocumentStatus.invalid)
      .length;

  void setMainTab(int index) {
    if (mainTabIndex == index) return;
    mainTabIndex = index;
    notifyListeners();
    if (isSignedIn && !mustChangePassword && index <= 3) {
      unawaited(refreshData(label: 'Refreshing documents...', soft: true));
    }
  }

  void openAssessment({int innerTab = 0}) {
    assessmentTabIndex = innerTab;
    notifyListeners();
  }

  void openSimulation() {
    mainTabIndex = 2;
    notifyListeners();
  }

  void openDocuments() {
    mainTabIndex = 1;
    notifyListeners();
  }

  void openNotifications() {
    mainTabIndex = 3;
    notifyListeners();
  }

  void openProfile() {
    mainTabIndex = 4;
    notifyListeners();
  }

  void setAssessmentTab(int index) {
    if (assessmentTabIndex == index) return;
    assessmentTabIndex = index;
    notifyListeners();
  }

  FacultyDocument? documentById(String id) {
    for (final doc in documents) {
      if (doc.id == id) return doc;
    }
    return null;
  }

  KraScore kraScore(KraType type) {
    return kraScores.firstWhere((k) => k.type == type);
  }

  Uint8List? bytesForDocument(String documentId) => localDocumentBytes[documentId];

  Future<Uint8List?> loadDocumentBytes(String documentId) async {
    final cached = localDocumentBytes[documentId];
    if (cached != null) return cached;
    if (_useMockAuthForTests || !isSignedIn) return null;
    try {
      final bytes = await _api.downloadFacultyDocumentBytes(documentId);
      final data = Uint8List.fromList(bytes);
      localDocumentBytes[documentId] = data;
      return data;
    } catch (_) {
      return null;
    }
  }

  Future<void> login(String email, String password) async {
    if (_useMockAuthForTests) {
      await Future<void>.delayed(const Duration(milliseconds: 350));
      MockAuth.validateSignIn(email, password, _activePassword);
      isSignedIn = true;
      mustChangePassword = false;
      signedInEmail = email.trim();
      _loadMockFixtureData();
      notifyListeners();
      return;
    }
    _clearLiveSessionData();
    final data = await _api.login(email: email, password: password);
    isSignedIn = true;
    mustChangePassword = AuthResponse.mustChangePassword(data);
    signedInEmail = AuthResponse.email(data) ?? email.trim();
    signedInUserId = AuthResponse.userId(data);
    await _syncFacultyWorkspace(skipProtectedApis: mustChangePassword);
    notifyListeners();
  }

  Future<bool> tryRestoreSession() async {
    if (_useMockAuthForTests || !_sessionRestoreEnabled) return false;
    final ok = await _api.tryRestoreSession();
    if (!ok) return false;
    final data = await _api.session();
    isSignedIn = true;
    mustChangePassword = AuthResponse.mustChangePassword(data);
    signedInUserId = AuthResponse.userId(data) ?? signedInUserId;
    signedInEmail = AuthResponse.email(data) ?? signedInEmail;
    await _syncFacultyWorkspace(skipProtectedApis: mustChangePassword);
    notifyListeners();
    return true;
  }

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    if (_useMockAuthForTests) {
      await Future<void>.delayed(const Duration(milliseconds: 250));
      if (currentPassword != _activePassword) {
        throw AppAuthException('The current password is incorrect.', statusCode: 400);
      }
      if (newPassword.length < 8) {
        throw AppAuthException('Use at least 8 characters.', statusCode: 400);
      }
      if (newPassword == _activePassword) {
        throw AppAuthException(
          'Choose a password that is different from your current password.',
          statusCode: 400,
        );
      }
      _activePassword = newPassword;
      mustChangePassword = false;
      notifyListeners();
      return;
    }
    final data = await _api.changePassword(
      currentPassword: currentPassword,
      newPassword: newPassword,
    );
    mustChangePassword = AuthResponse.mustChangePassword(data);
    signedInUserId = AuthResponse.userId(data) ?? signedInUserId;
    signedInEmail = AuthResponse.email(data) ?? signedInEmail;
    await _syncFacultyWorkspace();
    notifyListeners();
  }

  Future<String> requestAccount({required String fullName, required String email}) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    if (fullName.trim().isEmpty || email.trim().isEmpty) {
      throw AppAuthException('Name and email are required.', statusCode: 400);
    }
    return MockAuth.registerMessage;
  }

  Future<Map<String, dynamic>> requestPasswordResetCode(String email) async {
    if (_useMockAuthForTests) {
      await Future<void>.delayed(const Duration(milliseconds: 400));
      return MockAuth.requestPasswordReset(email);
    }
    return _api.requestPasswordReset(email);
  }

  Future<String> verifyPasswordResetCode(String email, String otp) async {
    if (_useMockAuthForTests) {
      await Future<void>.delayed(const Duration(milliseconds: 350));
      _pendingResetToken = MockAuth.verifyResetCode(email, otp);
      return _pendingResetToken!;
    }
    _pendingResetToken = await _api.verifyPasswordResetCode(email: email, code: otp);
    return _pendingResetToken!;
  }

  Future<String> resetPassword({
    required String email,
    required String resetToken,
    required String newPassword,
  }) async {
    if (_useMockAuthForTests) {
      await Future<void>.delayed(const Duration(milliseconds: 350));
      final message = MockAuth.resetPassword(
        resetToken: resetToken,
        newPassword: newPassword,
      );
      _activePassword = newPassword;
      _pendingResetToken = null;
      return message;
    }
    final message = await _api.resetPassword(
      email: email,
      resetToken: resetToken,
      newPassword: newPassword,
    );
    _pendingResetToken = null;
    return message;
  }

  Future<void> refreshData({String? label, bool soft = false}) async {
    if (!isSignedIn) return;
    final now = DateTime.now();
    if (soft &&
        _lastRefreshAt != null &&
        now.difference(_lastRefreshAt!) < const Duration(seconds: 20)) {
      return;
    }
    refreshInProgress = true;
    busyMessage = label ?? 'Refreshing...';
    notifyListeners();
    try {
      if (!_useMockAuthForTests) {
        await _syncFacultyWorkspace(quiet: true);
      }
      await Future<void>.delayed(const Duration(milliseconds: 200));
      _lastRefreshAt = DateTime.now();
    } finally {
      refreshInProgress = false;
      busyMessage = null;
      notifyListeners();
    }
  }

  Future<void> fetchDocumentsFromApi({bool quiet = false}) async {
    if (_useMockAuthForTests || !isSignedIn) return;
    try {
      final rows = await _api.fetchMyDocuments();
      documents = rows.map(FacultyDocument.fromApi).toList();
    } catch (_) {
      if (!quiet) rethrow;
    }
  }

  Future<void> fetchAssignedReviewer({bool quiet = false}) async {
    if (_useMockAuthForTests || !isSignedIn) {
      assignedReviewer = null;
      assignedReviewerError = null;
      assignedReviewerLoading = false;
      return;
    }
    if (!quiet) {
      assignedReviewerLoading = true;
      assignedReviewerError = null;
      notifyListeners();
    }
    try {
      final data = await _api.fetchMyAssignedReviewer();
      assignedReviewer = AssignedReviewer.fromApi(data);
      assignedReviewerError = null;
    } on AppAuthException catch (error) {
      assignedReviewer = null;
      assignedReviewerError = error.message;
    } catch (_) {
      assignedReviewer = null;
      assignedReviewerError = 'Could not load your assigned reviewer. Pull to refresh to try again.';
    } finally {
      assignedReviewerLoading = false;
      notifyListeners();
    }
  }

  Future<void> _syncFacultyWorkspace({
    bool skipProtectedApis = false,
    bool quiet = false,
  }) async {
    if (_useMockAuthForTests || !isSignedIn) return;
    try {
      final me = await _api.fetchFacultyMe();
      final profileJson = me['profile'];
      if (profileJson is Map<String, dynamic>) {
        faculty = FacultyProfile.fromApi(profileJson);
      }
      final user = me['user'];
      if (user is Map<String, dynamic>) {
        signedInEmail ??= user['email'] as String?;
      }
      _profileLoaded = faculty.fullName.trim().isNotEmpty;
    } catch (_) {
      if (!quiet) rethrow;
    }

    try {
      final dash = await _api.fetchFacultyDashboard();
      _dashboard = FacultyApiMapper.dashboardFromApi(dash, faculty);
      _kraScores = _dashboard!.kraScores;
      _simulation = _dashboard!.simulation;
      _preparationPeriod =
          FacultyApiMapper.preparationPeriodFromApi(dash['preparationPeriod'] as Map<String, dynamic>?);
    } catch (_) {
      _dashboard = null;
      _kraScores = null;
      _simulation = FacultySessionDefaults.unavailableSimulation(
        currentRank: faculty.currentRank,
        targetRank: faculty.targetRank,
      );
    }

    if (!skipProtectedApis) {
      await fetchAssignedReviewer(quiet: true);
      await fetchDocumentsFromApi(quiet: true);
    }
  }

  void _clearLiveSessionData() {
    faculty = FacultySessionDefaults.faculty;
    documents = const [];
    notifications = const [];
    _dashboard = null;
    _kraScores = null;
    _simulation = null;
    _requirements = null;
    _preparationPeriod = null;
    assignedReviewer = null;
    assignedReviewerError = null;
    assignedReviewerLoading = false;
    _profileLoaded = false;
    localDocumentBytes.clear();
  }

  void _loadMockFixtureData() {
    faculty = MockData.faculty;
    documents = List<FacultyDocument>.from(MockData.documents);
    notifications = List<AppNotification>.from(MockData.notifications);
    _dashboard = MockData.dashboard;
    _kraScores = MockData.kraScores;
    _simulation = MockData.simulation;
    _requirements = MockData.requirements;
    _preparationPeriod = MockData.preparationPeriod;
    assignedReviewer = null;
    assignedReviewerError = null;
    assignedReviewerLoading = false;
    _profileLoaded = true;
    localDocumentBytes.clear();
  }

  Future<T> _runExclusive<T>(String message, Future<T> Function() action) async {
    if (_operationLocked) {
      throw StateError('Another document operation is still running.');
    }
    _operationLocked = true;
    busyMessage = message;
    notifyListeners();
    try {
      return await action();
    } finally {
      _operationLocked = false;
      busyMessage = null;
      notifyListeners();
    }
  }

  Future<void> deleteDocument(String documentId) async {
    documents = documents.where((d) => d.id != documentId).toList();
    localDocumentBytes.remove(documentId);
    notifyListeners();
  }

  Future<FacultyDocument> replaceDocument({
    required String documentId,
    required String fileName,
    required List<int> fileBytes,
    String? title,
  }) async {
    return _runExclusive('Replacing document...', () async {
      await Future<void>.delayed(const Duration(milliseconds: 500));
      localDocumentBytes[documentId] = Uint8List.fromList(fileBytes);
      final index = documents.indexWhere((d) => d.id == documentId);
      if (index < 0) {
        throw StateError('Document not found.');
      }
      final existing = documents[index];
      final updated = FacultyDocument(
        id: existing.id,
        title: title ?? existing.title,
        category: existing.category,
        kra: existing.kra,
        submittedAt: DateTime.now(),
        status: DocumentStatus.pendingReview,
        points: existing.points,
        fileName: fileName,
        author: existing.author,
        extractedInfo: _simulatedExtraction(fileName),
        reviewerFeedback: existing.reviewerFeedback,
        validationResult:
            'Simulated re-upload. Reviewer verification is required before any score preview changes.',
        indicatorId: existing.indicatorId,
        criterionId: existing.criterionId,
        mimeType: existing.mimeType,
        fileSize: fileBytes.length,
        hasFile: true,
        fileUrl: existing.fileUrl,
        canDelete: existing.canDelete,
        canReplace: existing.canReplace,
        canRequestWithdrawal: existing.canRequestWithdrawal,
        effectiveSimulationScore: existing.effectiveSimulationScore,
        simulationScoreSource: existing.simulationScoreSource,
        reviewerOversightStatus: existing.reviewerOversightStatus,
        scoringStatus: existing.scoringStatus,
      );
      documents = [
        ...documents.sublist(0, index),
        updated,
        ...documents.sublist(index + 1),
      ];
      notifyListeners();
      return updated;
    });
  }

  Future<void> requestDocumentWithdrawal(String documentId, {String? reason}) async {
    await _runExclusive('Submitting withdrawal request...', () async {
      await Future<void>.delayed(const Duration(milliseconds: 350));
      notifications = [
        AppNotification(
          id: 'n-${DateTime.now().millisecondsSinceEpoch}',
          kind: NotificationKind.reviewerFeedback,
          message:
              'Simulated: withdrawal request recorded for document $documentId${reason != null && reason.isNotEmpty ? ' ($reason)' : ''}.',
          createdAt: DateTime.now(),
          visualState: NotificationVisualState.unread,
          relatedDocumentId: documentId,
        ),
        ...notifications,
      ];
      notifyListeners();
    });
  }

  Future<String?> uploadDocument({
    required String title,
    required DocumentCategory category,
    required KraType kra,
    required String fileName,
    String? kraWebId,
    String? criterionId,
    String? indicatorId,
    double? contributionPercent,
    String? packageId,
    int? requirementIndex,
    List<int>? fileBytes,
  }) async {
    return _runExclusive('Uploading document...', () async {
      if (!_useMockAuthForTests &&
          isSignedIn &&
          fileBytes != null &&
          kraWebId != null &&
          criterionId != null &&
          indicatorId != null) {
        final saved = await _api.uploadFacultyDocument(
          title: title,
          kraId: kraWebId,
          criterionId: criterionId,
          indicatorId: indicatorId,
          fileName: fileName,
          fileBytes: fileBytes,
        );
        final doc = FacultyDocument.fromApi(saved);
        localDocumentBytes[doc.id] = Uint8List.fromList(fileBytes);
        addSubmittedDocument(doc);
        return doc.id;
      }
      await Future<void>.delayed(const Duration(milliseconds: 600));
      final id = 'doc-${DateTime.now().millisecondsSinceEpoch}';
      if (fileBytes != null) {
        localDocumentBytes[id] = Uint8List.fromList(fileBytes);
      }
      addSubmittedDocument(
        FacultyDocument(
          id: id,
          title: title,
          category: category,
          kra: kra,
          submittedAt: DateTime.now(),
          status: DocumentStatus.draft,
          points: 0,
          fileName: fileName,
          criterionId: criterionId,
          indicatorId: indicatorId,
          hasFile: fileBytes != null,
          extractedInfo: _simulatedExtraction(fileName),
          validationResult:
              'Simulated submission (frontend only). OCR and scoring previews are not official.',
        ),
      );
      return packageId ?? 'pkg-sim-${DateTime.now().millisecondsSinceEpoch}';
    });
  }

  Future<FacultyDocument?> submitDocumentForReview(String documentId) async {
    if (_useMockAuthForTests || !isSignedIn) return null;
    final data = await _api.submitFacultyDocument(documentId);
    final row = data['document'] ?? data;
    if (row is! Map<String, dynamic>) return null;
    final updated = FacultyDocument.fromApi(row);
    final index = documents.indexWhere((d) => d.id == documentId);
    if (index >= 0) {
      documents = [
        ...documents.sublist(0, index),
        updated,
        ...documents.sublist(index + 1),
      ];
    }
    notifyListeners();
    return updated;
  }

  Map<String, String> _simulatedExtraction(String fileName) {
    return {
      'Extraction mode': 'Simulated preview (no server OCR)',
      'OCR excerpt': 'Sample placeholder text for $fileName — not extracted by Tesseract.',
      'Validation status': 'Needs Verification',
      'Reviewer oversight status': 'Pending simulated review',
      'Simulation score source': 'Sample UI data only',
      'Guideline': 'DBM–CHED Joint Circular No. 01, s. 2026 (UI reference)',
    };
  }

  void markNotificationRead(String id) {
    notifications = [
      for (final n in notifications)
        if (n.id == id)
          n.copyWith(visualState: NotificationVisualState.read)
        else
          n,
    ];
    notifyListeners();
  }

  void markAllNotificationsRead() {
    notifications = [
      for (final n in notifications)
        n.copyWith(visualState: NotificationVisualState.read),
    ];
    notifyListeners();
  }

  void clearNotifications() {
    notifications = [];
    notifyListeners();
  }

  void addSubmittedDocument(FacultyDocument document) {
    documents = [document, ...documents];
    notifications = [
      AppNotification(
        id: 'n-${DateTime.now().millisecondsSinceEpoch}',
        kind: NotificationKind.documentSubmitted,
        message: '${document.title} was submitted and is pending review.',
        createdAt: DateTime.now(),
        visualState: NotificationVisualState.unread,
        relatedDocumentId: document.id,
        relatedKra: document.kra,
      ),
      ...notifications,
    ];
    notifyListeners();
  }

  void updateFaculty(FacultyProfile updated) {
    faculty = updated;
    notifyListeners();
  }

  Future<void> saveFaculty(FacultyProfile updated) async {
    await Future<void>.delayed(const Duration(milliseconds: 200));
    faculty = updated;
    notifyListeners();
  }

  @visibleForTesting
  void prepareForWidgetTests() {
    _useMockAuthForTests = true;
    _sessionRestoreEnabled = false;
    isSignedIn = true;
    _loadMockFixtureData();
  }

  @visibleForTesting
  void resetAuthForTests() {
    _useMockAuthForTests = true;
    _activePassword = MockAuth.demoPassword;
    _pendingResetToken = null;
    _loadMockFixtureData();
  }

  Future<void> resetSession() async {
    if (isSignedIn && !_useMockAuthForTests) {
      try {
        await _api.logout();
      } catch (_) {
        /* clear local session even if API is unreachable */
      }
    }
    mainTabIndex = 0;
    assessmentTabIndex = 0;
    isSignedIn = false;
    mustChangePassword = false;
    signedInEmail = null;
    signedInUserId = null;
    _clearLiveSessionData();
    notifyListeners();
  }
}
