/**
 * Sample FacultyLink state for frontend-only development.
 * Not official institutional data; not synchronized with the mobile app.
 */
window.FL = window.FL || {};

FL.mockSeed = function () {
  const now = new Date().toISOString();
  return {
    users: [
      {
        id: "user-admin",
        email: "admin@facultylink.edu.ph",
        password: "Admin@2026",
        role: "administrator",
        name: "Ana Dela Cruz",
        office: "Office of the VP for Academic Affairs",
        contact: "+63 917 100 0001",
        specialization: "Academic policy and faculty development"
      },
      {
        id: "user-reviewer-1",
        email: "reviewer@facultylink.edu.ph",
        password: "Reviewer@2026",
        role: "reviewer",
        name: "Dr. Elena Reyes",
        office: "College of Education — Review Unit",
        contact: "+63 917 200 0002",
        specialization: "Instruction and KRA I verification",
        mustChangePassword: false
      },
      {
        id: "user-reviewer-2",
        email: "jose.mendoza@facultylink.edu.ph",
        password: "Reviewer@2026",
        role: "reviewer",
        name: "Prof. Jose Mendoza",
        office: "Research and Extension Review",
        contact: "+63 917 200 0003",
        specialization: "Research, extension, and professional development"
      }
    ],
    faculty: [
      {
        id: "fac-001",
        name: "Maria Santos",
        email: "maria.santos@university.edu.ph",
        employeeNo: "FL-2024-0847",
        rank: "Instructor I",
        department: "Department of Curriculum and Instruction",
        college: "College of Education",
        campus: "Main Campus",
        status: "Active",
        reviewerId: "user-reviewer-1",
        yearsOfService: 4,
        targetRank: "Instructor II"
      },
      {
        id: "fac-002",
        name: "Jason Baroro",
        email: "jason.baroro@university.edu.ph",
        employeeNo: "FL-2023-0312",
        rank: "Assistant Professor I",
        department: "Department of Engineering",
        college: "College of Engineering",
        campus: "Main Campus",
        status: "Active",
        reviewerId: "user-reviewer-2",
        yearsOfService: 7,
        targetRank: "Assistant Professor II"
      },
      {
        id: "fac-003",
        name: "Liza Fernandez",
        email: "liza.fernandez@university.edu.ph",
        employeeNo: "FL-2022-0198",
        rank: "Associate Professor III",
        department: "Department of Biology",
        college: "College of Science",
        campus: "Main Campus",
        status: "Active",
        reviewerId: "user-reviewer-1",
        yearsOfService: 12,
        targetRank: "Professor I"
      }
    ],
    documents: [
      {
        id: "DOC-2026-001",
        name: "ED101_Syllabus_SY2025-2026.pdf",
        title: "Course Syllabus — ED 101",
        facultyId: "fac-001",
        reviewerId: "user-reviewer-1",
        indicatorId: "kra1-b-module-sole",
        kraId: "kra1",
        status: "approved",
        dateSubmitted: "2026-01-12T08:30:00+08:00",
        extractedInfo: {
          "Extracted title": "Foundations of Education — ED 101",
          "Extracted names": "Maria Santos",
          "Academic year": "SY 2025–2026",
          "OCR excerpt": "Course syllabus instructional module sole author",
          "Simulation eligible": "yes",
          "System-calculated score": "8",
          "Reviewer oversight status": "Verified"
        },
        ocr: { status: "complete", title: "ED 101 Syllabus", content: "Instructional module sole author" },
        review: {
          indicatorId: "kra1-b-module-sole",
          kraId: "kra1",
          criterionId: "kra1-b",
          finalScore: 8,
          assignedScore: 8,
          contributionPercent: 100
        }
      },
      {
        id: "DOC-2026-002",
        name: "SET_Summary_AY2024.pdf",
        facultyId: "fac-001",
        reviewerId: "user-reviewer-1",
        indicatorId: "kra1-a-student",
        kraId: "kra1",
        status: "pending-review",
        dateSubmitted: "2026-02-03T14:10:00+08:00",
        extractedInfo: {
          "Extracted names": "Maria Santos",
          "Academic year": "AY 2024–2025",
          "Academic term": "Semester 1",
          "Extracted rating": "92",
          "OCR excerpt": "Student Evaluation Rating Summary FEDAF SET",
          "Reviewer oversight status": "Awaiting Reviewer Check"
        },
        ocr: { status: "complete", title: "SET Summary", content: "Student evaluation rating summary" }
      },
      {
        id: "DOC-2026-003",
        name: "Conference_Certificate_Revision.pdf",
        facultyId: "fac-001",
        reviewerId: "user-reviewer-1",
        indicatorId: "kra2-b-presentation",
        kraId: "kra2",
        status: "revision",
        dateSubmitted: "2026-01-28T11:00:00+08:00",
        extractedInfo: {
          "Extracted title": "National Research Conference Presentation",
          "Extracted names": "Maria Santos",
          "Extracted date": "2025-11-14",
          "OCR excerpt": "research presentation certificate conference",
          "Reviewer oversight status": "Requires Review"
        },
        ocr: { status: "complete", title: "Conference Certificate", content: "Research presentation" },
        review: { remarks: "Attach the official program page showing paper title and schedule." }
      },
      {
        id: "DOC-2026-004",
        name: "Journal_Article_2025.pdf",
        facultyId: "fac-002",
        reviewerId: "user-reviewer-2",
        indicatorId: "kra2-a-journal-sole",
        kraId: "kra2",
        status: "approved",
        dateSubmitted: "2025-12-05T09:00:00+08:00",
        extractedInfo: {
          "Extracted title": "Structural Analysis of Rural Bridges",
          "Extracted names": "Jason Baroro",
          "Extracted date": "2025",
          "Simulation eligible": "yes",
          "System-calculated score": "10"
        },
        ocr: { status: "complete", title: "Journal Article", content: "Peer-reviewed journal sole author" },
        review: { finalScore: 10, assignedScore: 10, contributionPercent: 100, indicatorId: "kra2-a-journal-sole", kraId: "kra2", criterionId: "kra2-a" }
      },
      {
        id: "DOC-2026-005",
        name: "Extension_Report_2025.pdf",
        facultyId: "fac-003",
        reviewerId: "user-reviewer-1",
        indicatorId: "kra3-a-linkage",
        kraId: "kra3",
        status: "reviewer-required",
        dateSubmitted: "2026-02-10T16:45:00+08:00",
        extractedInfo: {
          "Extracted title": "Barangay Science Literacy Program",
          "Extracted names": "Liza Fernandez",
          "Extracted date": "2025",
          "OCR excerpt": "extension community linkage report"
        },
        ocr: { status: "complete", title: "Extension Report", content: "Community extension linkage" }
      }
    ],
    notifications: [
      {
        id: "note-1",
        userId: "user-admin",
        title: "Pending verification queue",
        body: "3 documents are awaiting reviewer action across assigned faculty.",
        read: false,
        createdAt: now
      },
      {
        id: "note-2",
        userId: "user-reviewer-1",
        title: "New submission from Maria Santos",
        body: "SET Summary AY2024 is ready for review.",
        read: false,
        createdAt: now
      },
      {
        id: "note-3",
        userId: "user-reviewer-1",
        title: "Revision resubmission expected",
        body: "Conference certificate for Maria Santos still needs the official program.",
        read: true,
        createdAt: "2026-01-29T10:00:00+08:00"
      }
    ],
    audit: [
      {
        id: "audit-1",
        actorId: "user-admin",
        action: "Published KRA configuration",
        targetId: "kra-settings",
        detail: "Draft KRA weights saved for demonstration.",
        createdAt: "2026-02-01T09:00:00+08:00"
      }
    ],
    evaluationPeriods: [
      {
        id: "period-rank-2026",
        type: "Rank Upgrade",
        label: "Rank Upgrade · AY 2025–2026 cycle",
        startDate: "2026-06-02",
        endDate: "2026-09-15",
        submissionOpen: "2026-06-02",
        submissionClose: "2026-08-31",
        reviewOpen: "2026-06-15",
        reviewClose: "2026-09-12",
        status: "active",
        timezone: "Asia/Manila"
      },
      {
        id: "period-reclass-2025",
        type: "Reclassification",
        label: "Reclassification · closed sample period",
        startDate: "2025-03-01",
        endDate: "2025-05-30",
        submissionOpen: "2025-03-01",
        submissionClose: "2025-04-30",
        reviewOpen: "2025-04-01",
        reviewClose: "2025-05-15",
        status: "closed",
        timezone: "Asia/Manila"
      }
    ],
    kraSettings: {
      guidelineLabel: "DBM–CHED Joint Circular No. 01, s. 2026",
      status: "published",
      publishedAt: "2026-01-15T08:00:00+08:00",
      rankWeights: {}
    },
    simulations: [
      {
        id: "sim-001",
        facultyId: "fac-001",
        currentRank: "Instructor I",
        targetRank: "Instructor II",
        estimatedPoints: 72,
        verifiedPoints: 18,
        missingRequirements: "Complete SET/SEF semester records; revise conference certificate.",
        readiness: "Preparation in progress",
        simulatedAt: "2026-02-08T13:00:00+08:00"
      }
    ]
  };
};
