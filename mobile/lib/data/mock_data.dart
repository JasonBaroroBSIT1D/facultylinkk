import '../models/enums.dart';
import '../models/models.dart';

abstract final class MockData {
  /// Prototype sample for AY 2025–2026. Status is hardcoded (not computed).
  static final preparationPeriod = PreparationPeriod(
    cycleName: 'JC No. 01, s. 2026 · Aug 1, 2023 – Jul 31, 2026',
    startDate: DateTime(2026, 6, 2),
    endDate: DateTime(2026, 9, 15),
    reviewerAvailableUntil: DateTime(2026, 9, 12),
    status: PreparationPeriodStatus.closingSoon,
  );

  static const faculty = FacultyProfile(
    fullName: 'Maria Santos',
    facultyId: 'FL-2024-0847',
    email: 'maria.santos@university.edu.ph',
    department: 'Department of Curriculum and Instruction',
    college: 'College of Education',
    currentRank: 'Instructor I',
    targetRank: 'Instructor II',
    highestDegree: 'Master of Arts in Education',
    specialization: 'Curriculum and Instruction',
    yearsInService: 4,
    employmentStatus: 'Permanent',
    campus: 'Main Campus',
    phone: '+63 917 555 0847',
  );

  static final dashboard = DashboardSnapshot(
    totalPoints: 72,
    targetPoints: 100,
    documentCompletionPercent: 68,
    validatedCount: 5,
    pendingCount: 2,
    actionRequiredCount: 2,
    kraScores: kraScores,
    recentActivity: const [
      RecentActivity(
        title: 'Classroom Observation Report',
        subtitle: 'Submitted for Instruction',
        timeLabel: '2 hours ago',
        status: DocumentStatus.pendingReview,
      ),
      RecentActivity(
        title: 'Research Presentation Certificate',
        subtitle: 'Returned for revision',
        timeLabel: 'Yesterday',
        status: DocumentStatus.needsRevision,
      ),
      RecentActivity(
        title: 'Journal Article: Inquiry-Based Learning',
        subtitle: 'Validated · 10 points',
        timeLabel: '3 days ago',
        status: DocumentStatus.validated,
      ),
    ],
    recentFeedback: const [
      ReviewerFeedbackPreview(
        documentTitle: 'Research Presentation Certificate',
        message:
            'Please attach the official conference program showing your paper title and presentation schedule.',
        timeLabel: 'Yesterday',
      ),
      ReviewerFeedbackPreview(
        documentTitle: 'Thesis Advisership Record',
        message:
            'This file could not be validated. Upload the signed advisership certificate from the Graduate School.',
        timeLabel: '4 days ago',
      ),
    ],
    simulation: simulation,
  );

  static const kraScores = [
    KraScore(
      type: KraType.instruction,
      currentPoints: 25,
      targetPoints: 30,
      documentCount: 4,
      statusLabel: 'On track',
      breakdown: [
        KraBreakdownItem(
          title: 'Teaching effectiveness',
          points: 10,
          note: 'Student evaluation summaries and observation reports',
        ),
        KraBreakdownItem(
          title: 'Instructional materials',
          points: 8,
          note: 'Course syllabi and learning packets',
        ),
        KraBreakdownItem(
          title: 'Student advising',
          points: 7,
          note: 'Advisership and mentoring records',
        ),
      ],
    ),
    KraScore(
      type: KraType.research,
      currentPoints: 18,
      targetPoints: 30,
      documentCount: 2,
      statusLabel: 'Needs attention',
      breakdown: [
        KraBreakdownItem(
          title: 'Refereed publication',
          points: 10,
          note: 'Peer-reviewed journal article',
        ),
        KraBreakdownItem(
          title: 'Research presentation',
          points: 8,
          note: 'Awaiting revised conference certificate',
        ),
      ],
    ),
    KraScore(
      type: KraType.extension,
      currentPoints: 14,
      targetPoints: 20,
      documentCount: 2,
      statusLabel: 'In progress',
      breakdown: [
        KraBreakdownItem(
          title: 'Community literacy program',
          points: 8,
          note: 'Completed extension report with attendance',
        ),
        KraBreakdownItem(
          title: 'Barangay training facilitation',
          points: 6,
          note: 'Pending reviewer validation',
        ),
      ],
    ),
    KraScore(
      type: KraType.professionalDevelopment,
      currentPoints: 15,
      targetPoints: 20,
      documentCount: 2,
      statusLabel: 'On track',
      breakdown: [
        KraBreakdownItem(
          title: 'National certification',
          points: 5,
          note: 'TESDA National Certificate',
        ),
        KraBreakdownItem(
          title: 'Seminars and training',
          points: 10,
          note: 'CHED and in-service training certificates',
        ),
      ],
    ),
  ];

  static const simulation = RankSimulation(
    currentRank: 'Instructor I',
    targetRank: 'Instructor II',
    currentPoints: 72,
    requiredPoints: 100,
    eligibilityLabel: 'Potentially Eligible',
    areasToImprove: [
      ImprovementArea(
        kra: KraType.instruction,
        recommendedPoints: 5,
        guidance:
            'Add a complete instructional materials portfolio and a recent classroom observation.',
      ),
      ImprovementArea(
        kra: KraType.research,
        recommendedPoints: 8,
        guidance:
            'Revise the conference certificate and consider adding another refereed output.',
      ),
      ImprovementArea(
        kra: KraType.professionalDevelopment,
        recommendedPoints: 3,
        guidance:
            'Upload the latest in-service training certificate once processing is complete.',
      ),
    ],
  );

  static final documents = <FacultyDocument>[
    FacultyDocument(
      id: 'doc-001',
      title: 'Course Syllabus — ED 101, SY 2025–2026',
      category: DocumentCategory.teachingRecords,
      kra: KraType.instruction,
      submittedAt: DateTime(2026, 8, 12),
      status: DocumentStatus.validated,
      points: 8,
      fileName: 'ED101_Syllabus_SY2025-2026.pdf',
      author: 'Maria Santos',
      extractedInfo: const {
        'Document type': 'Course syllabus',
        'Course': 'ED 101 — Foundations of Education',
        'Academic year': 'SY 2025–2026',
        'Pages': '14',
      },
      validationResult: 'Document matches the submitted teaching record.',
    ),
    FacultyDocument(
      id: 'doc-002',
      title: 'Student Evaluation Summary, 1st Sem AY 2025–2026',
      category: DocumentCategory.teachingRecords,
      kra: KraType.instruction,
      submittedAt: DateTime(2026, 8, 10),
      status: DocumentStatus.validated,
      points: 6,
      fileName: 'SET_Summary_1S_2025.pdf',
      author: 'Office of Academic Affairs',
      extractedInfo: const {
        'Instrument': 'Student Evaluation of Teaching',
        'Term': '1st Semester AY 2025–2026',
        'Mean rating': '4.62 / 5.00',
      },
      validationResult: 'Official evaluation summary verified.',
    ),
    FacultyDocument(
      id: 'doc-003',
      title: 'Classroom Observation Report',
      category: DocumentCategory.teachingRecords,
      kra: KraType.instruction,
      submittedAt: DateTime(2026, 8, 27),
      status: DocumentStatus.pendingReview,
      points: 5,
      fileName: 'Classroom_Observation_Aug2026.pdf',
      author: 'Dept. Chair, Curriculum and Instruction',
      extractedInfo: const {
        'Observer': 'Prof. Elena Cruz',
        'Date of observation': 'August 18, 2026',
        'Course observed': 'ED 214',
      },
      validationResult: 'Awaiting reviewer confirmation.',
    ),
    FacultyDocument(
      id: 'doc-004',
      title: 'Journal Article: Inquiry-Based Learning in Basic Education',
      category: DocumentCategory.researchPublications,
      kra: KraType.research,
      submittedAt: DateTime(2026, 8, 4),
      status: DocumentStatus.validated,
      points: 10,
      fileName: 'Santos_Inquiry_Based_Learning_2025.pdf',
      author: 'Maria Santos',
      extractedInfo: const {
        'Publication type': 'Refereed journal article',
        'Journal': 'Philippine Journal of Education Studies',
        'Year': '2025',
        'ISSN': '2244-1180',
      },
      validationResult: 'Peer-reviewed publication accepted as research evidence.',
    ),
    FacultyDocument(
      id: 'doc-005',
      title: 'Research Presentation Certificate — National Research Forum',
      category: DocumentCategory.researchPublications,
      kra: KraType.research,
      submittedAt: DateTime(2026, 8, 20),
      status: DocumentStatus.needsRevision,
      points: 0,
      fileName: 'NRF_Presentation_Certificate.pdf',
      author: 'Maria Santos',
      extractedInfo: const {
        'Event': 'National Research Forum 2026',
        'Role': 'Paper presenter',
      },
      reviewerFeedback:
          'Please attach the official conference program showing your paper title and presentation schedule. The certificate alone does not identify the paper.',
      validationResult: 'Incomplete supporting evidence.',
    ),
    FacultyDocument(
      id: 'doc-006',
      title: 'Community Literacy Program Completion Report',
      category: DocumentCategory.extensionDocuments,
      kra: KraType.extension,
      submittedAt: DateTime(2026, 7, 28),
      status: DocumentStatus.validated,
      points: 8,
      fileName: 'Literacy_Program_Report_2026.pdf',
      author: 'Maria Santos; Barangay San Isidro',
      extractedInfo: const {
        'Program': 'Community Literacy for Parents',
        'Beneficiaries': '42 parents',
        'Duration': 'March–June 2026',
      },
      validationResult: 'Extension output verified with attendance and narrative report.',
    ),
    FacultyDocument(
      id: 'doc-007',
      title: 'Barangay Training Facilitation Certificate',
      category: DocumentCategory.extensionDocuments,
      kra: KraType.extension,
      submittedAt: DateTime(2026, 8, 22),
      status: DocumentStatus.pendingReview,
      points: 6,
      fileName: 'Brgy_Training_Facilitation.pdf',
      author: 'LGU San Isidro',
      extractedInfo: const {
        'Activity': 'Parenting education workshop',
        'Role': 'Lead facilitator',
      },
      validationResult: 'Awaiting reviewer confirmation.',
    ),
    FacultyDocument(
      id: 'doc-008',
      title: 'TESDA National Certificate — Bookkeeping',
      category: DocumentCategory.certifications,
      kra: KraType.professionalDevelopment,
      submittedAt: DateTime(2026, 6, 15),
      status: DocumentStatus.validated,
      points: 5,
      fileName: 'TESDA_NC_Bookkeeping.pdf',
      author: 'TESDA',
      extractedInfo: const {
        'Credential': 'National Certificate II',
        'Qualification': 'Bookkeeping',
        'Validity': '2024–2029',
      },
      validationResult: 'National certification accepted.',
    ),
    FacultyDocument(
      id: 'doc-009',
      title: 'CHED Seminar on Outcomes-Based Education',
      category: DocumentCategory.trainingCertificates,
      kra: KraType.professionalDevelopment,
      submittedAt: DateTime(2026, 8, 26),
      status: DocumentStatus.processing,
      points: 0,
      fileName: 'CHED_OBE_Seminar_Certificate.jpg',
      author: 'Commission on Higher Education',
      extractedInfo: const {
        'Status': 'System processing in progress',
        'Note': 'Text extraction is not yet complete in this prototype.',
      },
      validationResult: 'Queued for processing.',
    ),
    FacultyDocument(
      id: 'doc-010',
      title: 'Thesis Advisership Record — Graduate School',
      category: DocumentCategory.advisershipRecords,
      kra: KraType.instruction,
      submittedAt: DateTime(2026, 8, 8),
      status: DocumentStatus.invalid,
      points: 0,
      fileName: 'Advisership_Scan.jpg',
      author: 'Maria Santos',
      extractedInfo: const {
        'Student': 'Not clearly captured',
        'Role': 'Adviser (claimed)',
      },
      reviewerFeedback:
          'This file could not be validated. The scan is unreadable and does not include a Graduate School dry seal. Please upload the signed advisership certificate.',
      validationResult: 'Document could not be validated.',
    ),
    FacultyDocument(
      id: 'doc-011',
      title: 'Instructional Materials Portfolio (Draft)',
      category: DocumentCategory.teachingRecords,
      kra: KraType.instruction,
      submittedAt: DateTime(2026, 8, 18),
      status: DocumentStatus.needsRevision,
      points: 0,
      fileName: 'IM_Portfolio_Draft.pdf',
      author: 'Maria Santos',
      extractedInfo: const {
        'Contents': 'Lesson exemplars, worksheets',
        'Coverage': 'ED 101 only',
      },
      reviewerFeedback:
          'Please include materials for at least two courses and add the department chair’s endorsement page.',
      validationResult: 'Incomplete instructional materials set.',
    ),
  ];

  static final notifications = <AppNotification>[
    AppNotification(
      id: 'n-001',
      kind: NotificationKind.documentNeedsRevision,
      message:
          'Research Presentation Certificate needs a conference program before it can be validated.',
      createdAt: DateTime(2026, 8, 27, 9, 15),
      visualState: NotificationVisualState.actionRequired,
      relatedDocumentId: 'doc-005',
      relatedKra: KraType.research,
    ),
    AppNotification(
      id: 'n-002',
      kind: NotificationKind.missingRequirement,
      message:
          'Instruction is missing a complete instructional materials portfolio.',
      createdAt: DateTime(2026, 8, 27, 8, 40),
      visualState: NotificationVisualState.unread,
      relatedKra: KraType.instruction,
    ),
    AppNotification(
      id: 'n-003',
      kind: NotificationKind.documentSubmitted,
      message: 'Classroom Observation Report was submitted and is pending review.',
      createdAt: DateTime(2026, 8, 27, 7, 5),
      visualState: NotificationVisualState.unread,
      relatedDocumentId: 'doc-003',
    ),
    AppNotification(
      id: 'n-004',
      kind: NotificationKind.reviewerFeedback,
      message:
          'A reviewer left comments on Thesis Advisership Record. Action is required.',
      createdAt: DateTime(2026, 8, 24, 16, 20),
      visualState: NotificationVisualState.actionRequired,
      relatedDocumentId: 'doc-010',
    ),
    AppNotification(
      id: 'n-005',
      kind: NotificationKind.documentValidated,
      message:
          'Journal Article: Inquiry-Based Learning in Basic Education has been validated (+10 points).',
      createdAt: DateTime(2026, 8, 24, 11, 0),
      visualState: NotificationVisualState.read,
      relatedDocumentId: 'doc-004',
    ),
    AppNotification(
      id: 'n-006',
      kind: NotificationKind.kraScoreUpdated,
      message: 'Your Instruction KRA preview is now 25 points.',
      createdAt: DateTime(2026, 8, 23, 14, 10),
      visualState: NotificationVisualState.read,
      relatedKra: KraType.instruction,
    ),
    AppNotification(
      id: 'n-007',
      kind: NotificationKind.rankSimulationUpdated,
      message:
          'Rank upgrade simulation refreshed. You are 28 points from Instructor II (mock preview).',
      createdAt: DateTime(2026, 8, 22, 10, 0),
      visualState: NotificationVisualState.read,
    ),
  ];

  static const requirements = <RequirementItem>[
    RequirementItem(
      id: 'req-i-1',
      title: 'Student evaluation of teaching',
      description: 'Official SET summary for the latest rating period.',
      kra: KraType.instruction,
      status: RequirementStatus.completed,
    ),
    RequirementItem(
      id: 'req-i-2',
      title: 'Course syllabus',
      description: 'Updated syllabus for a handled course in the current academic year.',
      kra: KraType.instruction,
      status: RequirementStatus.completed,
    ),
    RequirementItem(
      id: 'req-i-3',
      title: 'Classroom observation',
      description: 'Signed observation report from the department chair or dean.',
      kra: KraType.instruction,
      status: RequirementStatus.pending,
      hint: 'Your observation report is currently pending review.',
    ),
    RequirementItem(
      id: 'req-i-4',
      title: 'Instructional materials portfolio',
      description: 'Endorsed set of instructional materials covering at least two courses.',
      kra: KraType.instruction,
      status: RequirementStatus.needsRevision,
      hint: 'Revise the draft portfolio using the reviewer’s comments.',
    ),
    RequirementItem(
      id: 'req-r-1',
      title: 'Refereed research publication',
      description: 'Peer-reviewed journal article or equivalent research output.',
      kra: KraType.research,
      status: RequirementStatus.completed,
    ),
    RequirementItem(
      id: 'req-r-2',
      title: 'Research presentation',
      description: 'Certificate plus official program for a research presentation.',
      kra: KraType.research,
      status: RequirementStatus.needsRevision,
      hint: 'Attach the conference program with your paper title.',
    ),
    RequirementItem(
      id: 'req-r-3',
      title: 'Additional research output',
      description: 'A second refereed paper, creative work, or funded research involvement.',
      kra: KraType.research,
      status: RequirementStatus.missing,
      hint: 'This is the largest remaining gap toward Instructor II in this preview.',
    ),
    RequirementItem(
      id: 'req-e-1',
      title: 'Completed extension program',
      description: 'Narrative report, attendance, and proof of community partnership.',
      kra: KraType.extension,
      status: RequirementStatus.completed,
    ),
    RequirementItem(
      id: 'req-e-2',
      title: 'Community training or service',
      description: 'Certificate or documentation of facilitated community training.',
      kra: KraType.extension,
      status: RequirementStatus.pending,
    ),
    RequirementItem(
      id: 'req-e-3',
      title: 'Impact or sustainability note',
      description: 'Short statement of outcomes or follow-through with the partner community.',
      kra: KraType.extension,
      status: RequirementStatus.missing,
    ),
    RequirementItem(
      id: 'req-p-1',
      title: 'National or professional certification',
      description: 'Valid professional license or national certificate.',
      kra: KraType.professionalDevelopment,
      status: RequirementStatus.completed,
    ),
    RequirementItem(
      id: 'req-p-2',
      title: 'Relevant seminar or training',
      description: 'Recent CHED, university, or professional training certificate.',
      kra: KraType.professionalDevelopment,
      status: RequirementStatus.pending,
      hint: 'Your OBE seminar certificate is still being processed.',
    ),
    RequirementItem(
      id: 'req-p-3',
      title: 'Membership or continuing education',
      description: 'Proof of professional organization membership or continuing education units.',
      kra: KraType.professionalDevelopment,
      status: RequirementStatus.missing,
    ),
  ];

  /// Sample KRA I Criterion A preview (simulated UI — not computed by a server).
  static Map<String, dynamic> get criterionASample => {
        'set': {
          'filledCount': 5,
          'requiredSemesters': 6,
          'averageRating': 4.15,
          'points': 14,
          'maxPoints': 36,
          'finalized': false,
        },
        'sef': {
          'filledCount': 4,
          'requiredSemesters': 6,
          'averageRating': 4.0,
          'points': 9,
          'maxPoints': 24,
          'finalized': false,
        },
        'criterionPoints': 23,
        'criterionMax': 60,
      };
}
