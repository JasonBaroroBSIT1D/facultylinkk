/**
 * FacultyLink — predefined evaluation rules.
 * Source: DBM–CHED Joint Circular No. 01, s. 2026 (Enhanced Implementing Guidelines
 * of DBM–CHED JC No. 3, s. 2022), dated 18 May 2026 — Annex A scoring matrix.
 * Point values, maximums, evidence, and conditions follow that circular.
 * Contribution for co-authored outputs is the percentage declared by the authors;
 * it is not a fixed split invented by FacultyLink.
 * Final Score = Base Points × Contribution Percentage (FacultyLink scoring relationship,
 * consistent with the circular’s contribution rules).
 */
window.FL = window.FL || {};

FL.rules = {
  citation: "DBM–CHED Joint Circular No. 01, s. 2026 (Enhanced Implementing Guidelines of JC No. 3, s. 2022)",
  annex: "JC No. 01, s. 2026 — Annex A (Criteria, Points, and Required Evidence)",
  evaluationPeriod: "August 1, 2023 – July 31, 2026",
  formula: "Final Score = Base Points × Contribution Percentage",
  formulaNote: "For an output with two or more claimants, each faculty declares a contribution percentage on the prescribed Certificate of Contribution form. Points received equal the points allocated for the indicator multiplied by that percentage. A sole author, sole inventor, or sole developer is credited the full base points.",
  globalConditions: [
    "Faculty are evaluated on Instruction; Research, Innovation and/or Creative Work; Extension; and Professional Development within the evaluation period (August 1, 2023 – July 31, 2026, and succeeding three-year cycles unless CHED and DBM provide otherwise).",
    "Only performance and accomplishments within the prescribed evaluation period are given points.",
    "There shall be no double counting of points. A single document used for one indicator cannot be used for another, unless specifically permitted (for example, a paper presented and published in an indexed journal in the same period may earn both presentation and research points).",
    "Outputs must be aligned with the faculty member’s field of specialization or allied field, unless otherwise specified.",
    "All declarations must be supported by the documentary evidence required under the circular.",
    "The SUC governing board has the final authority on reclassification decisions. FacultyLink does not replace that decision."
  ],
  kras: [
    {
      id: "kra1",
      code: "KRA I",
      name: "Instruction",
      maxPoints: 100,
      summary: "A faculty may earn a total of 100 points from Criteria A (60), B (30), and C (10).",
      criteria: [
        {
          id: "kra1-a",
          name: "Criterion A — Teaching Effectiveness",
          maxPoints: 60,
          description: "Ability to design and implement instructional strategies that enhance student learning, assessed through SET (60%) and SEF (40%).",
          indicators: [
            {
              id: "kra1-a-student",
              name: "Student Evaluation of Teachers (SET) (60%)",
              pointsLabel: "OSETR ÷ 100 × 36",
              maxPoints: 36,
              contribution: "not-applicable",
              formula: {
                type: "rating",
                multiplier: 36
              },
              evidence: [
                "Student Evaluation Rating Summary / FEDAF using the prescribed template"
              ],
              conditions: [
                "SET Points = (OSETR ÷ 100) × 36, where OSETR is the Overall SET Rating and 36 is 60% of the 60-point criterion maximum.",
                "For AY 2023–2024 and 2024–2025, NBC 461 QCE instrument results (transmuted from a 25-point scale to 100) remain recognized.",
                "Starting the first semester of AY 2025–2026, SUCs may implement CMO No. 19, s. 2025; mandatory from the second semester of AY 2025–2026 onward, with FEDAF as the required document.",
                "Special-status divisor rules in Section 10 apply (study leave, maternity leave, sabbatical, newly appointed faculty, laboratory schools)."
              ]
            },
            {
              id: "kra1-a-supervisor",
              name: "Supervisor’s Evaluation of Faculty (SEF) (40%)",
              pointsLabel: "OSEFR ÷ 100 × 24",
              maxPoints: 24,
              contribution: "not-applicable",
              formula: {
                type: "rating",
                multiplier: 24
              },
              evidence: [
                "Supervisor’s Evaluation Rating / FEDAF using the prescribed template"
              ],
              conditions: [
                "SEF Points = (OSEFR ÷ 100) × 24, where OSEFR is the Overall SEF Rating and 24 is 40% of the 60-point criterion maximum.",
                "Teaching Effectiveness Points (TEP) = SET Points + SEF Points."
              ]
            }
          ]
        },
        {
          id: "kra1-b",
          name: "Criterion B — Instructional Materials Development and Academic Programs",
          maxPoints: 30,
          description: "Instructional materials developed and approved for use, and academic degree programs developed or substantially revised and implemented by the SUC.",
          indicators: [
            {
              id: "kra1-b-textbook-sole",
              name: "Sole author of a textbook",
              points: 30,
              maxPoints: 30,
              contribution: "sole",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings"
              ],
              conditions: [
                "A textbook is an exposition of generally accepted principles in one subject, intended primarily as a basis for instruction (RA 8047).",
                "Must be published by an SUC press, academic press, or registered educational publishing company and approved for use by the SUC.",
                "Must be original work (not a mere compilation), aligned with the faculty’s field, evaluated by IMDC or equivalent, listed in the syllabus, and in library holdings.",
                "In the next evaluation cycle, the textbook must also be duly copyrighted."
              ]
            },
            {
              id: "kra1-b-textbook-co",
              name: "Co-author of a textbook",
              points: 30,
              pointsLabel: "% contribution × 30",
              maxPoints: 30,
              contribution: "declared",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings",
                "Certificate of Contribution Form_IM (Annex C), signed by all co-authors and certified by the dean"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra1-b-module-sole",
              name: "Sole author of a module",
              points: 16,
              maxPoints: 16,
              contribution: "sole",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings"
              ],
              conditions: [
                "A stand-alone module covering all topics for an entire course, or a complete series/set of modules within a course, earns full points.",
                "Incomplete sets are not awarded points."
              ]
            },
            {
              id: "kra1-b-module-co",
              name: "Co-author of a module",
              points: 16,
              pointsLabel: "% contribution × 16",
              maxPoints: 16,
              contribution: "declared",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings",
                "Certificate of Contribution Form_IM (Annex C), signed by all co-authors and certified by the dean"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra1-b-manual-sole",
              name: "Sole author of an instructional manual",
              points: 16,
              maxPoints: 16,
              contribution: "sole",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings"
              ],
              conditions: [
                "A stand-alone instructional manual covering an entire course, or a complete series/set, earns full points.",
                "Incomplete sets are not awarded points."
              ]
            },
            {
              id: "kra1-b-manual-co",
              name: "Co-author of an instructional manual",
              points: 16,
              pointsLabel: "% contribution × 16",
              maxPoints: 16,
              contribution: "declared",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings",
                "Certificate of Contribution Form_IM (Annex C), signed by all co-authors and certified by the dean"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra1-b-multimedia-sole",
              name: "Sole author of multimedia teaching materials",
              points: 16,
              maxPoints: 16,
              contribution: "sole",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings",
                "Proof of originality (concept note/instructional design rationale; timestamped project files; and/or raw source files)",
                "Proof of pedagogical validity (expert/peer validation and/or documented student feedback)"
              ],
              conditions: [
                "Simple compilations of video-recorded PowerPoint lectures without substantive instructional design are not considered.",
                "For this cycle, any of the originality and pedagogical-validity proofs may be submitted; subsequent cycles require all."
              ]
            },
            {
              id: "kra1-b-multimedia-co",
              name: "Co-author of multimedia teaching materials",
              points: 16,
              pointsLabel: "% contribution × 16",
              maxPoints: 16,
              contribution: "declared",
              evidence: [
                "Copy of the instructional material developed (complete set where applicable)",
                "Evidence of IMDC (or equivalent) evaluation and approval for use",
                "Approved syllabus or course guide listing the material as a reference",
                "Librarian certification that the material is in library holdings",
                "Certificate of Contribution Form_IM (Annex C), signed by all co-authors and certified by the dean",
                "Proof of originality",
                "Proof of pedagogical validity"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra1-b-program-lead",
              name: "Academic program developed or revised — Lead",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Documentary proof of contribution (feasibility study, benchmarking, program outcomes, curriculum design/OBE mapping, stakeholder consultation)",
                "Certification signed by the Dean specifying the faculty’s role as lead",
                "Academic Council and Governing Board resolutions",
                "Valid RRPA or COPC, as applicable"
              ],
              conditions: [
                "Committee members claiming this indicator may not also claim administrative-designation points for the same committee under Criterion D of Extension."
              ]
            },
            {
              id: "kra1-b-program-contributor",
              name: "Academic program developed or revised — Contributor",
              points: 5,
              maxPoints: 5,
              contribution: "not-applicable",
              evidence: [
                "Documentary proof of contribution",
                "Certification signed by the Dean specifying the faculty’s role as contributor",
                "Academic Council and Governing Board resolutions",
                "Valid RRPA or COPC, as applicable"
              ],
              conditions: [
                "Committee members claiming this indicator may not also claim administrative-designation points for the same committee under Criterion D of Extension."
              ]
            }
          ]
        },
        {
          id: "kra1-c",
          name: "Criterion C — Research Advising and Mentorship Services",
          maxPoints: 10,
          description: "Service as adviser or panel member for student research, and mentorship/coaching of competition winners.",
          indicators: [
            {
              id: "kra1-c-adviser-sp",
              name: "Adviser — Special Project or Capstone Project",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Topic must be within or closely related to the faculty’s field.",
                "Project must be successfully completed.",
                "Advising loads generally involve up to five students per academic year."
              ]
            },
            {
              id: "kra1-c-adviser-ut",
              name: "Adviser — Undergraduate Thesis",
              points: 5,
              maxPoints: 5,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Topic must be within or closely related to the faculty’s field.",
                "Thesis must be successfully completed."
              ]
            },
            {
              id: "kra1-c-adviser-mt",
              name: "Adviser — Master’s Thesis",
              points: 8,
              maxPoints: 8,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Topic must be within or closely related to the faculty’s field.",
                "Thesis must be successfully completed."
              ]
            },
            {
              id: "kra1-c-adviser-dd",
              name: "Adviser — Doctoral Dissertation",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Topic must be within or closely related to the faculty’s field.",
                "Dissertation must be successfully completed."
              ]
            },
            {
              id: "kra1-c-panel-sp",
              name: "Panel — Special Project or Capstone Project",
              points: 1,
              maxPoints: 1,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Program must have RRPA or COPC as applicable."
              ]
            },
            {
              id: "kra1-c-panel-ut",
              name: "Panel — Undergraduate Thesis",
              points: 1,
              maxPoints: 1,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Program must have RRPA or COPC as applicable."
              ]
            },
            {
              id: "kra1-c-panel-mt",
              name: "Panel — Master’s Thesis",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Program must have RRPA or COPC as applicable."
              ]
            },
            {
              id: "kra1-c-panel-dd",
              name: "Panel — Doctoral Dissertation",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Approval sheet",
                "RRPA or COPC for the program"
              ],
              conditions: [
                "Program must have RRPA or COPC as applicable."
              ]
            },
            {
              id: "kra1-c-mentor",
              name: "Mentor or coach of a student or team",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Official designation or appointment as mentor/coach from the SUC President",
                "Evidence of major prize (Champion, 1st, 2nd, or 3rd Place) at regional, national, or international level",
                "Publicly available competition mechanics"
              ],
              conditions: [
                "Local competitions and consolation prizes are not eligible.",
                "Competition must align with the faculty’s field of specialization.",
                "Only competitions sponsored by reputable private entities, professional organizations with national membership, consortia of SUCs, or equivalent recognized sponsors are considered."
              ]
            }
          ]
        }
      ]
    },
    {
      id: "kra2",
      code: "KRA II",
      name: "Research, Innovation and/or Creative Work",
      maxPoints: 100,
      summary: "A faculty may reach 100 points from one criterion or from a combination of Criteria A, B, and C. Each criterion has a maximum of 100 points; the KRA total cannot exceed 100.",
      criteria: [
        {
          id: "kra2-a",
          name: "Criterion A — Research Outputs Published",
          maxPoints: 100,
          description: "Scholarly research outputs published, translated into project/policy/product, or cited in indexed journals.",
          indicators: [
            {
              id: "kra2-a-book-sole",
              name: "Sole author of an academic book",
              points: 100,
              maxPoints: 100,
              contribution: "sole",
              evidence: [
                "Copy of the published academic book showing author, date, and title",
                "Evidence of peer review and publication by a reputable academic or university press"
              ],
              conditions: [
                "A book is a printed non-periodical of at least 48 pages exclusive of covers (UNESCO / RA 8047).",
                "Must present original research or scholarly work in an academic discipline.",
                "Textbooks are credited under Instructional Materials, not here.",
                "Institutional review prior to publication is required starting the next evaluation cycle."
              ]
            },
            {
              id: "kra2-a-book-co",
              name: "Co-author of an academic book",
              points: 100,
              pointsLabel: "% contribution × 100",
              maxPoints: 100,
              contribution: "declared",
              evidence: [
                "Copy of the published academic book",
                "Certificate of Contribution Form_Research Output (Annex D), signed by all co-authors and certified by the Research Director"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-a-chapter-sole",
              name: "Sole author of an edited academic book chapter",
              points: 35,
              maxPoints: 35,
              contribution: "sole",
              evidence: [
                "Copy of the published chapter showing author, date, and book title",
                "Evidence of peer review"
              ],
              conditions: [
                "Scholarly or scientific chapters in edited volumes published by a reputable academic press."
              ]
            },
            {
              id: "kra2-a-chapter-co",
              name: "Co-author of an edited academic book chapter",
              points: 35,
              pointsLabel: "% contribution × 35",
              maxPoints: 35,
              contribution: "declared",
              evidence: [
                "Copy of the published chapter",
                "Certificate of Contribution Form_Research Output (Annex D)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-a-journal-sole",
              name: "Sole author of a journal article",
              points: 50,
              maxPoints: 50,
              contribution: "sole",
              evidence: [
                "Copy of the published article showing author, date, and journal title"
              ],
              conditions: [
                "Published in a journal indexed in Scopus, Web of Science, or ASEAN Citation Index (ACI accepted through its last issue in 2024).",
                "Student co-authorship requires a governing-board policy allowing it."
              ]
            },
            {
              id: "kra2-a-journal-co",
              name: "Co-author of a journal article",
              points: 50,
              pointsLabel: "% contribution × 50",
              maxPoints: 50,
              contribution: "declared",
              evidence: [
                "Copy of the published article",
                "Certificate of Contribution Form_Research Output (Annex D)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-a-monograph-sole",
              name: "Sole author of an academic monograph",
              points: 100,
              maxPoints: 100,
              contribution: "sole",
              evidence: [
                "Copy of the published monograph",
                "Evidence of peer review"
              ],
              conditions: [
                "Peer-reviewed academic monograph published by a reputable press."
              ]
            },
            {
              id: "kra2-a-monograph-co",
              name: "Co-author of an academic monograph",
              points: 100,
              pointsLabel: "% contribution × 100",
              maxPoints: 100,
              contribution: "declared",
              evidence: [
                "Copy of the published monograph",
                "Certificate of Contribution Form_Research Output (Annex D)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-a-translation-sole",
              name: "Research translated into a project, policy, or product — Sole / Lead",
              points: 35,
              maxPoints: 70,
              contribution: "sole",
              evidence: [
                "Completed research output that served as basis",
                "Evidence of presentation, publication, or official submission",
                "Description of the project/policy/product and proof of approval, completion, or utilization"
              ],
              conditions: [
                "Category maximum is 70 points.",
                "There must be clear evidence that the research informed the project, policy, or product."
              ],
              groupMax: {
                group: "kra2-a-translation",
                max: 70
              }
            },
            {
              id: "kra2-a-translation-co",
              name: "Research translated into a project, policy, or product — Co-contributor",
              points: 35,
              pointsLabel: "% contribution × 35",
              maxPoints: 70,
              contribution: "declared",
              evidence: [
                "Completed research output and translation evidence",
                "Certificate of Contribution Form_Translated Research (Annex E)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ],
              groupMax: {
                group: "kra2-a-translation",
                max: 70
              }
            },
            {
              id: "kra2-a-cite",
              name: "Research publication cited",
              points: 10,
              maxPoints: 60,
              contribution: "not-applicable",
              evidence: [
                "Copy of the faculty’s cited article published in a Scopus-, WoS-, or ACI-indexed journal",
                "Copy of the citing article also published in a Scopus-, WoS-, or ACI-indexed journal",
                "Certification from the Research Director attesting indexing at the time of publication"
              ],
              conditions: [
                "10 points per cited article, maximum 60 points.",
                "Self-citations are not counted.",
                "Both the cited and citing articles must be in Scopus, WoS, or ACI at the time of their publication."
              ],
              groupMax: {
                group: "kra2-a-cite",
                max: 60
              }
            }
          ]
        },
        {
          id: "kra2-b",
          name: "Criterion B — Inventions",
          maxPoints: 100,
          description: "Patentable inventions, commercialized patented products, utility models, industrial designs, and non-patentable products.",
          indicators: [
            {
              id: "kra2-b-patent-a-sole",
              name: "Invention patent — Acceptance (sole inventor)",
              points: 10,
              maxPoints: 10,
              contribution: "sole",
              evidence: [
                "Photo of the invention",
                "Special Order signed by the President",
                "Formality Examination Report with no noted defects from IPOPHL"
              ],
              conditions: [
                "Only the highest patent stage attained within the evaluation period is credited."
              ]
            },
            {
              id: "kra2-b-patent-a-co",
              name: "Invention patent — Acceptance (co-inventor)",
              points: 10,
              pointsLabel: "% contribution × 10",
              maxPoints: 10,
              contribution: "declared",
              evidence: [
                "IPOPHL acceptance documents",
                "Certificate of Contribution Form_Intellectual Property (Annex F)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-b-patent-p-sole",
              name: "Invention patent — Publication (sole inventor)",
              points: 20,
              maxPoints: 20,
              contribution: "sole",
              evidence: [
                "Photo of the invention",
                "Special Order signed by the President",
                "Substantive Examination Report / notice of publication from IPOPHL"
              ],
              conditions: [
                "Only the highest patent stage attained within the evaluation period is credited."
              ]
            },
            {
              id: "kra2-b-patent-p-co",
              name: "Invention patent — Publication (co-inventor)",
              points: 20,
              pointsLabel: "% contribution × 20",
              maxPoints: 20,
              contribution: "declared",
              evidence: [
                "IPOPHL publication documents",
                "Certificate of Contribution Form_Intellectual Property (Annex F)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-b-patent-g-sole",
              name: "Invention patent — Grant (sole inventor)",
              points: 80,
              maxPoints: 80,
              contribution: "sole",
              evidence: [
                "Photo of the invention",
                "Special Order signed by the President",
                "Patent Certificate issued by IPOPHL"
              ],
              conditions: [
                "Only the highest patent stage attained within the evaluation period is credited."
              ]
            },
            {
              id: "kra2-b-patent-g-co",
              name: "Invention patent — Grant (co-inventor)",
              points: 80,
              pointsLabel: "% contribution × 80",
              maxPoints: 80,
              contribution: "declared",
              evidence: [
                "IPOPHL patent certificate",
                "Certificate of Contribution Form_Intellectual Property (Annex F)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-b-comm-local",
              name: "Commercialized patented product — Local",
              points: 5,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Photo of the patented product",
                "Invention Patent Certificate",
                "CPR or equivalent / licensing agreement",
                "Proof of commercialization",
                "Certification from Research Director / ITSO"
              ],
              conditions: [
                "5 points, maximum 20.",
                "Local means commercialized within the Philippines.",
                "First commercialization must fall within the evaluation period."
              ],
              groupMax: {
                group: "kra2-b-comm-local",
                max: 20
              }
            },
            {
              id: "kra2-b-comm-intl",
              name: "Commercialized patented product — International",
              points: 10,
              maxPoints: 30,
              contribution: "not-applicable",
              evidence: [
                "Photo of the patented product",
                "Invention Patent Certificate",
                "Licensing or technology-transfer agreement",
                "Proof of commercialization outside the Philippines",
                "Certification from Research Director / ITSO"
              ],
              conditions: [
                "10 points, maximum 30.",
                "International means commercialized in at least one country outside the Philippines."
              ],
              groupMax: {
                group: "kra2-b-comm-intl",
                max: 30
              }
            },
            {
              id: "kra2-b-um-sole",
              name: "Utility model — Registration (sole inventor)",
              points: 10,
              maxPoints: 10,
              contribution: "sole",
              evidence: [
                "Photo of the utility model",
                "Special Order signed by the President",
                "UM Certificate of Registration from IPOPHL"
              ],
              conditions: [
                "For this cycle, points are awarded for UMs registered within the evaluation period; subsequent cycles use implementation as the basis."
              ]
            },
            {
              id: "kra2-b-um-co",
              name: "Utility model — Registration (co-inventor)",
              points: 10,
              pointsLabel: "% contribution × 10",
              maxPoints: 10,
              contribution: "declared",
              evidence: [
                "UM certificate",
                "Certificate of Contribution Form_Intellectual Property (Annex F)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-b-id-sole",
              name: "Industrial design — Registration (sole inventor)",
              points: 5,
              maxPoints: 5,
              contribution: "sole",
              evidence: [
                "Photo of the industrial design",
                "Special Order signed by the President",
                "ID Certificate of Registration from IPOPHL"
              ],
              conditions: [
                "For this cycle, points are awarded for IDs registered within the evaluation period; subsequent cycles use implementation as the basis."
              ]
            },
            {
              id: "kra2-b-id-co",
              name: "Industrial design — Registration (co-inventor)",
              points: 5,
              pointsLabel: "% contribution × 5",
              maxPoints: 5,
              contribution: "declared",
              evidence: [
                "ID certificate",
                "Certificate of Contribution Form_Intellectual Property (Annex F)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-b-sw-new-sole",
              name: "New copyrighted and utilized software — Sole developer",
              points: 10,
              maxPoints: 10,
              contribution: "sole",
              evidence: [
                "Special Order signed by the President",
                "Project summary",
                "User manual / design / source documentation",
                "Copyright Certificate from IPOPHL",
                "End-user utilization certification"
              ],
              conditions: [
                "The software must be both copyrighted and utilized."
              ]
            },
            {
              id: "kra2-b-sw-new-co",
              name: "New copyrighted and utilized software — Co-developer",
              points: 10,
              pointsLabel: "% contribution × 10",
              maxPoints: 10,
              contribution: "declared",
              evidence: [
                "Same software evidence",
                "Certificate of Contribution Form_Software (Annex G)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-b-sw-upd-sole",
              name: "Updated copyrighted and utilized software — Sole developer",
              points: 4,
              maxPoints: 4,
              contribution: "sole",
              evidence: [
                "Special Order signed by the President",
                "Project summary",
                "Copyright Certificate from IPOPHL",
                "End-user utilization certification",
                "Description of substantial new functionalities not in the previous version"
              ],
              conditions: [
                "Updated products must add substantial new functionalities, features, or modules."
              ]
            },
            {
              id: "kra2-b-sw-upd-co",
              name: "Updated copyrighted and utilized software — Co-developer",
              points: 4,
              pointsLabel: "% contribution × 4",
              maxPoints: 4,
              contribution: "declared",
              evidence: [
                "Same updated-software evidence",
                "Certificate of Contribution Form_Software (Annex G)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-b-variety-sole",
              name: "New plant variety, animal breed, or microbial strain — Sole developer",
              points: 10,
              maxPoints: 10,
              contribution: "sole",
              evidence: [
                "Photo",
                "Registration / deposit certificate from the authorized agency",
                "Certification of propagation, breeding, or culture validation"
              ],
              conditions: [
                "Must be registered with the appropriate authority and propagated or reproduced."
              ]
            },
            {
              id: "kra2-b-variety-co",
              name: "New plant variety, animal breed, or microbial strain — Co-developer",
              points: 10,
              pointsLabel: "% contribution × 10",
              maxPoints: 10,
              contribution: "declared",
              evidence: [
                "Registration / deposit evidence",
                "Certificate of Contribution Form_New Cultivars, Breeds and Strains (Annex H)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            }
          ]
        },
        {
          id: "kra2-c",
          name: "Criterion C — Creative Works",
          maxPoints: 100,
          description: "Creative works produced, performed, presented, exhibited, or published in the performing arts, visual arts, film, and literary arts.",
          indicators: [
            {
              id: "kra2-c-music-comp-sole",
              name: "Musical composition",
              points: 20,
              maxPoints: 20,
              contribution: "sole",
              evidence: [
                "Published original musical score and/or copyright registration",
                "Proof of invitation/acceptance",
                "Proof of first performance"
              ],
              conditions: [
                "Only the first performance earns points."
              ]
            },
            {
              id: "kra2-c-music-comp-co",
              name: "Musical composition — Co-composer",
              points: 20,
              pointsLabel: "% contribution × 20",
              maxPoints: 20,
              contribution: "declared",
              evidence: [
                "Same composition evidence",
                "Certificate of Contribution Form_Creative Works (Annex I)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-c-music-arr-sole",
              name: "Musical arrangement",
              points: 20,
              maxPoints: 20,
              contribution: "sole",
              evidence: [
                "Published arranged or original arrangement score",
                "Proof of invitation/acceptance",
                "Proof of first performance",
                "Dean/Program Director certification of role where applicable"
              ],
              conditions: [
                "Covers adaptation and original arrangement."
              ]
            },
            {
              id: "kra2-c-music-arr-co",
              name: "Musical arrangement — Co-arranger",
              points: 20,
              pointsLabel: "% contribution × 20",
              maxPoints: 20,
              contribution: "declared",
              evidence: [
                "Same arrangement evidence",
                "Certificate of Contribution Form_Creative Works (Annex I)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-c-music-perf",
              name: "Musical performance (vocal or instrumental)",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Proof of invitation/acceptance",
                "Proof of performance",
                "Organizer/conductor/director certification"
              ],
              conditions: [
                "Only the first performance of the work in the evaluation context is credited as applicable under Section 27."
              ]
            },
            {
              id: "kra2-c-conducting",
              name: "Conducting",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Proof of invitation/acceptance as conductor",
                "Proof of performance",
                "Organizer/music director certification"
              ],
              conditions: [
                "Academic recitals, concerts, musical theatre, festivals, competitions, or professional/public venues."
              ]
            },
            {
              id: "kra2-c-music-prod-sole",
              name: "Music production",
              points: 20,
              maxPoints: 20,
              contribution: "sole",
              evidence: [
                "Produced music track with clear producer credit",
                "Copyright registration",
                "Published release details",
                "Dean certification of role and scope"
              ],
              conditions: [
                "For original work produced."
              ]
            },
            {
              id: "kra2-c-music-prod-co",
              name: "Music production — Co-producer",
              points: 20,
              pointsLabel: "% contribution × 20",
              maxPoints: 20,
              contribution: "declared",
              evidence: [
                "Same production evidence",
                "Certificate of Contribution Form_Creative Works (Annex I)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-c-choreo-sole",
              name: "Original choreography",
              points: 20,
              maxPoints: 20,
              contribution: "sole",
              evidence: [
                "Choreographic notations or written description",
                "Proof of invitation/acceptance",
                "Proof of first performance",
                "Organizer certification"
              ],
              conditions: [
                "Only the first performance earns points."
              ]
            },
            {
              id: "kra2-c-choreo-co",
              name: "Original choreography — Co-choreographer",
              points: 20,
              pointsLabel: "% contribution × 20",
              maxPoints: 20,
              contribution: "declared",
              evidence: [
                "Same choreography evidence",
                "Certificate of Contribution Form_Creative Works (Annex I)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-c-dance-perf",
              name: "Dance performance",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Proof of dance performance",
                "Certification from choreographer, artistic director, or department head"
              ],
              conditions: [
                "Academic events, recitals, concerts, festivals, competitions, productions, or professional/public venues."
              ]
            },
            {
              id: "kra2-c-playwright-sole",
              name: "Playwright",
              points: 20,
              maxPoints: 20,
              contribution: "sole",
              evidence: [
                "Full script",
                "Copyright registration",
                "Proof of invitation/acceptance",
                "Proof of production",
                "Director certification"
              ],
              conditions: [
                "Only the first production is credited."
              ]
            },
            {
              id: "kra2-c-playwright-co",
              name: "Playwright — Co-author",
              points: 20,
              pointsLabel: "% contribution × 20",
              maxPoints: 20,
              contribution: "declared",
              evidence: [
                "Same playwright evidence",
                "Certificate of Contribution Form_Creative Works (Annex I)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-c-directing",
              name: "Theatrical directing",
              points: 20,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Proof of invitation/acceptance as director",
                "Event program or flyer",
                "Video/photo documentation",
                "Production manager certification"
              ],
              conditions: [
                "Staged theatrical production."
              ]
            },
            {
              id: "kra2-c-acting",
              name: "Acting",
              points: 20,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Proof of invitation/acceptance as actor",
                "Program/playbill/cast list",
                "Video/photo documentation",
                "Director or production manager certification"
              ],
              conditions: [
                "Staged theatrical production."
              ]
            },
            {
              id: "kra2-c-prod-design",
              name: "Production design",
              points: 20,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Proof of invitation/acceptance as designer",
                "Design portfolio",
                "Photo/video of realized design",
                "Program credits",
                "Director or production manager certification"
              ],
              conditions: [
                "Set, costume, lighting, or props design."
              ]
            },
            {
              id: "kra2-c-visual",
              name: "Visual arts exhibition (painting, drawing, mixed media, sculpture, photography, digital art)",
              points: 20,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Photograph of the exhibited work with title, description, date, and venue",
                "Proof of invitation/acceptance",
                "Exhibition catalog/brochure/program",
                "Gallery information",
                "Curator or gallery director certification"
              ],
              conditions: [
                "Exhibition in a formal venue.",
                "Only the first exhibition of the work earns points."
              ]
            },
            {
              id: "kra2-c-arch-design",
              name: "Architectural, engineering, or interior design (exhibition or juried)",
              points: 20,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Design proposal or project portfolio",
                "Proof of invitation/acceptance or peer/jury evaluation",
                "Exhibition or competition documentation",
                "Authorship documentation",
                "Information on the gallery, event, or organizing body"
              ],
              conditions: [
                "Covers exhibition and juried/peer-reviewed tracks under Section 27."
              ]
            },
            {
              id: "kra2-c-film",
              name: "Film (short, feature, documentary, experimental, animated)",
              points: 20,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Copy or working link to the film",
                "Proof of invitation/acceptance or festival entry",
                "Festival program or screening announcement with role credit",
                "Festival organizer certification"
              ],
              conditions: [
                "Faculty role may include director, producer, screenwriter, or cinematographer as credited."
              ]
            },
            {
              id: "kra2-c-novel-sole",
              name: "Literary publication — Novel",
              points: 20,
              maxPoints: 20,
              contribution: "sole",
              evidence: [
                "Copy of the published and copyrighted novel",
                "Publisher guidelines and evidence of editorial review",
                "Proof of publisher credibility"
              ],
              conditions: [
                "Published by a reputable press or publisher."
              ]
            },
            {
              id: "kra2-c-novel-co",
              name: "Literary publication — Novel (co-author)",
              points: 20,
              pointsLabel: "% contribution × 20",
              maxPoints: 20,
              contribution: "declared",
              evidence: [
                "Same novel evidence",
                "Certificate of Contribution Form_Creative Works (Annex I)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-c-story-sole",
              name: "Literary publication — Short story",
              points: 10,
              maxPoints: 10,
              contribution: "sole",
              evidence: [
                "Copy of the anthology, literary magazine, or journal issue",
                "Publisher guidelines and evidence of editorial review",
                "Proof of publisher credibility"
              ],
              conditions: [
                "Published in an anthology, literary journal, or literary magazine."
              ]
            },
            {
              id: "kra2-c-story-co",
              name: "Literary publication — Short story (co-author)",
              points: 10,
              pointsLabel: "% contribution × 10",
              maxPoints: 10,
              contribution: "declared",
              evidence: [
                "Same short-story evidence",
                "Certificate of Contribution Form_Creative Works (Annex I)"
              ],
              conditions: [
                "Points received = points allocated for the indicator × declared contribution percentage."
              ]
            },
            {
              id: "kra2-c-poetry",
              name: "Literary publication — Poetry",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Copy of the anthology, literary magazine, or journal issue",
                "Publisher guidelines and evidence of editorial review",
                "Proof of publisher credibility"
              ],
              conditions: [
                "2 points per published poem collection/entry under Annex A.",
                "Published in an anthology, literary journal, or literary magazine."
              ]
            },
            {
              id: "kra2-c-essay",
              name: "Literary publication — Literary essay",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Copy of the anthology, literary magazine, or journal issue",
                "Publisher guidelines and evidence of editorial review",
                "Proof of publisher credibility"
              ],
              conditions: [
                "2 points per published literary essay under Annex A."
              ]
            }
          ]
        }
      ]
    },
    {
      id: "kra3",
      code: "KRA III",
      name: "Extension Services",
      maxPoints: 100,
      bonusMax: 20,
      summary: "A faculty may earn 100 points from Criteria A (30), B (50), and C (20). Criterion D may add up to 20 bonus points; the final KRA total still cannot exceed 100.",
      criteria: [
        {
          id: "kra3-a",
          name: "Criterion A — Service to the Institution",
          maxPoints: 30,
          description: "Successful linkages, networking, and partnerships, and contribution to income generation.",
          indicators: [
            {
              id: "kra3-a-linkage",
              name: "Successful linkage, networking, or partnership activity",
              points: 5,
              maxPoints: 5,
              contribution: "not-applicable",
              evidence: [
                "Board/President/Chancellor approval authorizing the partnership",
                "Notarized MOA/MOU (or project proposal if activities are not in the MOA)",
                "Implementation or terminal report acknowledging successful implementation",
                "Certification from the President or concerned Vice President that the partnership was initiated through the faculty’s initiative"
              ],
              conditions: [
                "Partnership must be formalized and successfully implemented."
              ]
            },
            {
              id: "kra3-a-income-lead-100k",
              name: "Income generation — Lead — ₱100,000 and below",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Lead receives full points for the income band.",
                "Income may come from commercialization, external grants through project proposals, or industry-based projects."
              ]
            },
            {
              id: "kra3-a-income-lead-500k",
              name: "Income generation — Lead — ₱100,001 to ₱500,000",
              points: 4,
              maxPoints: 4,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Lead receives full points for the income band."
              ]
            },
            {
              id: "kra3-a-income-lead-6m",
              name: "Income generation — Lead — ₱500,001 to ₱6,000,000",
              points: 6,
              maxPoints: 6,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Lead receives full points for the income band."
              ]
            },
            {
              id: "kra3-a-income-lead-12m",
              name: "Income generation — Lead — ₱6,000,001 to ₱12,000,000",
              points: 12,
              maxPoints: 12,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Lead receives full points for the income band."
              ]
            },
            {
              id: "kra3-a-income-lead-over",
              name: "Income generation — Lead — Above ₱12,000,000",
              points: 18,
              maxPoints: 18,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Lead receives full points for the income band."
              ]
            },
            {
              id: "kra3-a-income-co-100k",
              name: "Income generation — Contributor — ₱100,000 and below",
              points: 1,
              maxPoints: 1,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Co-contributors each receive half of the Lead points for the same income band."
              ]
            },
            {
              id: "kra3-a-income-co-500k",
              name: "Income generation — Contributor — ₱100,001 to ₱500,000",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Co-contributors each receive half of the Lead points for the same income band."
              ]
            },
            {
              id: "kra3-a-income-co-6m",
              name: "Income generation — Contributor — ₱500,001 to ₱6,000,000",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Co-contributors each receive half of the Lead points for the same income band."
              ]
            },
            {
              id: "kra3-a-income-co-12m",
              name: "Income generation — Contributor — ₱6,000,001 to ₱12,000,000",
              points: 6,
              maxPoints: 6,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Co-contributors each receive half of the Lead points for the same income band."
              ]
            },
            {
              id: "kra3-a-income-co-over",
              name: "Income generation — Contributor — Above ₱12,000,000",
              points: 9,
              maxPoints: 9,
              contribution: "not-applicable",
              evidence: [
                "Financial reports / Sub-ARO or equivalent",
                "Finance Division certification of contribution"
              ],
              conditions: [
                "Co-contributors each receive half of the Lead points for the same income band."
              ]
            }
          ]
        },
        {
          id: "kra3-b",
          name: "Criterion B — Service to the Community",
          maxPoints: 50,
          description: "Professional and expertise-based services, media services, and institutional social responsibility / extension projects.",
          indicators: [
            {
              id: "kra3-b-qa-local",
              name: "Accreditation, evaluation, or assessment — Local",
              points: 8,
              maxPoints: 8,
              contribution: "not-applicable",
              evidence: [
                "Official appointment/designation",
                "Proof of actual engagement",
                "SUC President authorization"
              ],
              conditions: [
                "Points are earned per agency or organization engaged, not per deployment."
              ]
            },
            {
              id: "kra3-b-qa-intl",
              name: "Accreditation, evaluation, or assessment — International",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Official appointment/designation",
                "Proof of actual engagement",
                "SUC President authorization"
              ],
              conditions: [
                "Points are earned per organization, not per deployment."
              ]
            },
            {
              id: "kra3-b-judge-research",
              name: "Judge or examiner — Research awards",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Official invitation",
                "Proof of award/competition",
                "Proof of engagement",
                "President/VP authorization"
              ],
              conditions: [
                "Points are earned for every engagement during the cycle."
              ]
            },
            {
              id: "kra3-b-judge-academic",
              name: "Judge or examiner — Academic competitions",
              points: 1,
              maxPoints: 1,
              contribution: "not-applicable",
              evidence: [
                "Official invitation",
                "Proof of competition",
                "Proof of engagement",
                "President/VP authorization"
              ],
              conditions: [
                "Sponsored by a recognized agency or organization."
              ]
            },
            {
              id: "kra3-b-consult-local",
              name: "Short-term consultant or expert — Local",
              points: 8,
              maxPoints: 8,
              contribution: "not-applicable",
              evidence: [
                "Written agreement/contract/invitation with acceptance",
                "Evidence of engagement",
                "President/Chancellor/VP authorization"
              ],
              conditions: [
                "Includes editor, peer reviewer, statistician, proposal evaluator, adjunct faculty, or technical expert of a government agency."
              ]
            },
            {
              id: "kra3-b-consult-intl",
              name: "Short-term consultant or expert — International",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Written agreement/contract/invitation with acceptance",
                "Evidence of engagement",
                "President/Chancellor/VP authorization"
              ],
              conditions: [
                "Educational, technological, professional, scientific, or cultural activity sponsored by a private organization or government."
              ]
            },
            {
              id: "kra3-b-column-occasional",
              name: "Writer of an occasional newspaper column",
              points: 2,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Compiled newspaper articles",
                "Corresponding front pages showing publication name and date"
              ],
              conditions: [
                "2 points per published article, maximum 10."
              ],
              groupMax: {
                group: "kra3-b-column-occasional",
                max: 10
              }
            },
            {
              id: "kra3-b-column-regular",
              name: "Writer of a regular newspaper column",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Compiled articles of the regular column",
                "Corresponding front pages"
              ],
              conditions: [
                "Points are earned per regular column."
              ]
            },
            {
              id: "kra3-b-host",
              name: "Host of a television or radio program",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Contract, invitation, or similar document",
                "On-air schedule"
              ],
              conditions: [
                "Points are earned per regular program."
              ]
            },
            {
              id: "kra3-b-guest",
              name: "Guesting as a technical expert",
              points: 1,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Invitation letter"
              ],
              conditions: [
                "1 point per guesting, maximum 10."
              ],
              groupMax: {
                group: "kra3-b-guest",
                max: 10
              }
            },
            {
              id: "kra3-b-train-local",
              name: "Resource person, convenor, facilitator, moderator, or speaker — Local, per hour",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Invitation letter",
                "Program",
                "Certificate of appreciation or similar"
              ],
              conditions: [
                "2 points for every hour.",
                "Service must be at the tertiary or higher level."
              ]
            },
            {
              id: "kra3-b-train-intl",
              name: "Resource person, convenor, facilitator, moderator, or speaker — International, per hour",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Invitation letter",
                "Program",
                "Certificate of appreciation or similar"
              ],
              conditions: [
                "3 points for every hour.",
                "Service must be at the tertiary or higher level."
              ]
            },
            {
              id: "kra3-b-ext-head",
              name: "Head of an extension or production / ISR project",
              points: 5,
              maxPoints: 30,
              contribution: "not-applicable",
              evidence: [
                "Approval for the activity",
                "Appointment or designation as head",
                "Extension or production activity report"
              ],
              conditions: [
                "5 points per project, maximum 30 under Institutional Social Responsibility.",
                "Activity must be relevant to the faculty’s field."
              ],
              groupMax: {
                group: "kra3-b-ext-head",
                max: 30
              }
            },
            {
              id: "kra3-b-ext-participant",
              name: "Participant in an extension or production / ISR project",
              points: 2,
              maxPoints: 30,
              contribution: "not-applicable",
              evidence: [
                "Approval for the activity",
                "Extension or production activity report"
              ],
              conditions: [
                "2 points per project, maximum 30 under Institutional Social Responsibility."
              ],
              groupMax: {
                group: "kra3-b-ext-participant",
                max: 30
              }
            }
          ]
        },
        {
          id: "kra3-c",
          name: "Criterion C — Relevance and Quality of Extension Services",
          maxPoints: 20,
          description: "Client satisfaction rating for outreach and extension projects.",
          indicators: [
            {
              id: "kra3-c-satisfaction",
              name: "Client satisfaction rating for outreach and extension projects",
              pointsLabel: "Overall CSR ÷ 100 × 20",
              maxPoints: 20,
              contribution: "not-applicable",
              formula: {
                type: "rating",
                multiplier: 20
              },
              evidence: [
                "Summary of client satisfaction / CSR ratings for the evaluation period using the prescribed instrument"
              ],
              conditions: [
                "Points = (Overall CSR ÷ 100) × 20.",
                "Projects claimed here must also be declared under Institutional Social Responsibility in Criterion B.",
                "Follow the CMO / institutional instrument phasing in Section 35 for the applicable evaluation years."
              ]
            }
          ]
        },
        {
          id: "kra3-d",
          name: "Criterion D — Bonus Criterion (Administrative Designation)",
          maxPoints: 20,
          bonus: true,
          description: "Bonus points for administrative designations held for at least one continuous year within the evaluation period. Points are credited per year for each such designation. OIC service of at least one year is likewise credited. Committee creation must be Governing Board-approved.",
          indicators: [
            {
              id: "kra3-d-president",
              name: "President or OIC President",
              points: 20,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level.",
                "At least one continuous year within the evaluation period.",
                "Points are credited per year."
              ]
            },
            {
              id: "kra3-d-vp",
              name: "Vice-President",
              points: 15,
              maxPoints: 15,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year, minimum one continuous year."
              ]
            },
            {
              id: "kra3-d-chancellor",
              name: "Chancellor",
              points: 10,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-vc",
              name: "Vice-Chancellor",
              points: 8,
              maxPoints: 8,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-campus",
              name: "Campus Director or Administrator",
              points: 8,
              maxPoints: 8,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-regent",
              name: "Faculty Trustee or Regent",
              points: 8,
              maxPoints: 8,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Annual report of the faculty association"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-director",
              name: "Office Director",
              points: 6,
              maxPoints: 6,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-usec",
              name: "University or College Secretary",
              points: 6,
              maxPoints: 6,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-project",
              name: "Project Head (institution level)",
              points: 4,
              maxPoints: 4,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-inst-chair",
              name: "Institution-level committee — Chair",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Committee creation must be Governing Board-approved.",
                "Per year."
              ]
            },
            {
              id: "kra3-d-inst-member",
              name: "Institution-level committee — Member",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Committee creation must be Governing Board-approved.",
                "Per year."
              ]
            },
            {
              id: "kra3-d-inst-coord",
              name: "Coordinator (institution level)",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Institutional level. Per year."
              ]
            },
            {
              id: "kra3-d-dean",
              name: "Dean",
              points: 6,
              maxPoints: 6,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "College/department level. Per year."
              ]
            },
            {
              id: "kra3-d-adean",
              name: "Associate Dean",
              points: 5,
              maxPoints: 5,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "College/department level. Per year."
              ]
            },
            {
              id: "kra3-d-csec",
              name: "College Secretary",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "College/department level. Per year."
              ]
            },
            {
              id: "kra3-d-dept",
              name: "Department Head",
              points: 4,
              maxPoints: 4,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "College/department level. Per year."
              ]
            },
            {
              id: "kra3-d-chair",
              name: "Program Chair or Project Head (department level)",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "College/department level. Per year."
              ]
            },
            {
              id: "kra3-d-dept-chair",
              name: "Department-level committee — Chair",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Committee creation must be Governing Board-approved.",
                "Per year."
              ]
            },
            {
              id: "kra3-d-dept-member",
              name: "Department-level committee — Member",
              points: 1,
              maxPoints: 1,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "Committee creation must be Governing Board-approved.",
                "Per year."
              ]
            },
            {
              id: "kra3-d-dept-coord",
              name: "Coordinator (college/department level)",
              points: 1,
              maxPoints: 1,
              contribution: "not-applicable",
              evidence: [
                "Appointment or designation with effectivity period",
                "Accomplishment report"
              ],
              conditions: [
                "College/department level. Per year."
              ]
            }
          ]
        }
      ]
    },
    {
      id: "kra4",
      code: "KRA IV",
      name: "Professional Development",
      maxPoints: 100,
      bonusMax: 20,
      summary: "A faculty may earn 100 points from Criteria A (20), B (60), and C (20). Newly appointed faculty may receive up to 20 additional points under Criterion D; the final KRA total still cannot exceed 100.",
      criteria: [
        {
          id: "kra4-a",
          name: "Criterion A — Involvement in Professional Organizations",
          maxPoints: 20,
          description: "Membership and active participation in registered professional organizations and societies aligned with the faculty’s discipline, specialization, or designation.",
          indicators: [
            {
              id: "kra4-a-member",
              name: "Membership and active participation in a registered professional organization",
              points: 5,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Valid certificate of membership or ID",
                "For non-APO organizations: SEC registration, organizational profile (mandate, national membership, ≥10 years existence), and evidence of annual conventions for the past three years",
                "Evidence of active engagement beyond mere attendance"
              ],
              conditions: [
                "5 points per organization with active involvement, within the 20-point criterion maximum.",
                "Organization must be aligned with the faculty’s discipline, specialization, or designation.",
                "PRC AIPOs, SEC-registered national organizations meeting Section 38 qualifications, and multidisciplinary bodies such as NRCP and NAST are recognized."
              ],
              groupMax: {
                group: "kra4-a-member",
                max: 20
              }
            }
          ]
        },
        {
          id: "kra4-b",
          name: "Criterion B — Continuing Development",
          maxPoints: 60,
          description: "Educational qualifications, capacity-building participation, and paper presentations.",
          indicators: [
            {
              id: "kra4-b-postmaster",
              name: "Post-master diploma or certificate",
              points: 10,
              maxPoints: 40,
              contribution: "not-applicable",
              evidence: [
                "CAV TOR / diploma / certificate; CHED equivalency for foreign degrees when required"
              ],
              conditions: [
                "Counted within the educational-qualification and Criterion B caps.",
                "Honorary degrees and non-CHED-recognized programs are not considered."
              ],
              groupMax: {
                group: "kra4-b-educ",
                max: 40
              }
            },
            {
              id: "kra4-b-postdoc",
              name: "Post-doctorate diploma or certificate",
              points: 10,
              maxPoints: 40,
              contribution: "not-applicable",
              evidence: [
                "CAV TOR / diploma / certificate; CHED equivalency for foreign degrees when required"
              ],
              conditions: [
                "Counted within the educational-qualification cap."
              ],
              groupMax: {
                group: "kra4-b-educ",
                max: 40
              }
            },
            {
              id: "kra4-b-masters",
              name: "Additional master’s degree",
              points: 20,
              maxPoints: 40,
              contribution: "not-applicable",
              evidence: [
                "CAV TOR / diploma / certificate; CHED equivalency for foreign degrees when required"
              ],
              conditions: [
                "Postgraduate qualifications earned and submitted for reclassification."
              ],
              groupMax: {
                group: "kra4-b-educ",
                max: 40
              }
            },
            {
              id: "kra4-b-doctorate",
              name: "Doctorate degree or additional doctorate degree",
              points: 40,
              maxPoints: 40,
              contribution: "not-applicable",
              evidence: [
                "CAV TOR / diploma / certificate; CHED equivalency for foreign degrees when required"
              ],
              conditions: [
                "Automatic one sub-rank for a qualifying first doctorate is governed by Section 45 and is applied through the official evaluation process, not by FacultyLink.",
                "A doctorate that does not meet automatic-sub-rank conditions may still earn points here."
              ],
              groupMax: {
                group: "kra4-b-educ",
                max: 40
              }
            },
            {
              id: "kra4-b-part-local",
              name: "Participation in a conference, seminar, workshop, or capacity-building activity — Local",
              points: 1,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Certificate of participation",
                "Evidence of Presidential / Governing Board approval as required"
              ],
              conditions: [
                "1 point per activity, maximum 10.",
                "Minimum total duration of six (6) hours; multi-day activities under one theme count as one activity.",
                "Virtual structured programs require at least eight (8) hours and a reputable host."
              ],
              groupMax: {
                group: "kra4-b-part",
                max: 10
              }
            },
            {
              id: "kra4-b-part-intl",
              name: "Participation in a conference, seminar, workshop, or capacity-building activity — International",
              points: 2,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Certificate of participation",
                "Evidence of approval as required"
              ],
              conditions: [
                "2 points per activity, maximum 10 within the same participation cap."
              ],
              groupMax: {
                group: "kra4-b-part",
                max: 10
              }
            },
            {
              id: "kra4-b-paper-local",
              name: "Paper presentation in a conference — Local",
              points: 3,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Letter or certificate of acceptance",
                "Evidence of approval to present"
              ],
              conditions: [
                "3 points per presentation, maximum 10.",
                "A paper presented and also published in Scopus/WoS/ACI in the same period may earn both presentation points and KRA II research points."
              ],
              groupMax: {
                group: "kra4-b-paper",
                max: 10
              }
            },
            {
              id: "kra4-b-paper-intl",
              name: "Paper presentation in a conference — International",
              points: 5,
              maxPoints: 10,
              contribution: "not-applicable",
              evidence: [
                "Letter or certificate of acceptance",
                "Evidence of approval to present",
                "Evidence that at least three countries are represented among speakers and/or participants"
              ],
              conditions: [
                "5 points per presentation, maximum 10."
              ],
              groupMax: {
                group: "kra4-b-paper",
                max: 10
              }
            }
          ]
        },
        {
          id: "kra4-c",
          name: "Criterion C — Awards and Recognition",
          maxPoints: 20,
          description: "Awards of distinction in the faculty member’s specialization, profession, or assignment.",
          indicators: [
            {
              id: "kra4-c-inst",
              name: "Institutional award",
              points: 2,
              maxPoints: 2,
              contribution: "not-applicable",
              evidence: [
                "Short description of the award",
                "Certificate or photo of plaque/trophy/medal",
                "Organization profile",
                "Evidence that SUC PRAISE Guidelines are CSC-approved"
              ],
              conditions: [
                "Institutional awards under Section 43."
              ]
            },
            {
              id: "kra4-c-local",
              name: "Local and regional award (city, municipality, or province)",
              points: 3,
              maxPoints: 3,
              contribution: "not-applicable",
              evidence: [
                "Short description of the award",
                "Certificate or photo of plaque/trophy/medal",
                "Award criteria and mechanics",
                "Selection process",
                "Award-giving organization profile"
              ],
              conditions: [
                "Local and regional awards share this point value under Annex A."
              ]
            },
            {
              id: "kra4-c-national",
              name: "National award",
              points: 4,
              maxPoints: 4,
              contribution: "not-applicable",
              evidence: [
                "Short description of the award",
                "Certificate or photo of plaque/trophy/medal",
                "Award criteria and mechanics",
                "Selection process",
                "Award-giving organization profile"
              ],
              conditions: [
                "National awards under Section 43 earn 4 KRA points.",
                "Prestigious national/international awards that qualify for automatic one sub-rank under Section 46 are handled separately from this point value."
              ]
            }
          ]
        },
        {
          id: "kra4-d",
          name: "Criterion D — Additional Points for Newly Appointed Faculty",
          maxPoints: 20,
          bonus: true,
          description: "Applicable to newly appointed faculty who have not yet undergone reclassification. Points are for every year of prior full-time academic or industry experience; fractional years are proportional by months.",
          indicators: [
            {
              id: "kra4-d-pres",
              name: "Full-time academic service — President, per year",
              points: 5,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Service record, certificate of employment, notice of appointment/designation, or similar",
                "Brief job description"
              ],
              conditions: [
                "Newly appointed faculty only.",
                "Fractional years earn proportionate points."
              ],
              groupMax: {
                group: "kra4-d",
                max: 20
              }
            },
            {
              id: "kra4-d-vp",
              name: "Full-time academic service — Vice President, Dean, or Director, per year",
              points: 4,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Service record or certificate of employment",
                "Brief job description"
              ],
              conditions: [
                "Newly appointed faculty only."
              ],
              groupMax: {
                group: "kra4-d",
                max: 20
              }
            },
            {
              id: "kra4-d-head",
              name: "Full-time academic service — Department or Program Head, per year",
              points: 3,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Service record or certificate of employment",
                "Brief job description"
              ],
              conditions: [
                "Newly appointed faculty only."
              ],
              groupMax: {
                group: "kra4-d",
                max: 20
              }
            },
            {
              id: "kra4-d-faculty",
              name: "Full-time academic service — Faculty member, per year",
              points: 2,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Service record or certificate of employment",
                "Brief job description"
              ],
              conditions: [
                "Newly appointed faculty only."
              ],
              groupMax: {
                group: "kra4-d",
                max: 20
              }
            },
            {
              id: "kra4-d-mgr",
              name: "Industry experience — Managerial or supervisory, per year",
              points: 4,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Service record, certificate of employment, or notice of appointment",
                "Brief job description"
              ],
              conditions: [
                "Newly appointed faculty only.",
                "Non-academic organization."
              ],
              groupMax: {
                group: "kra4-d",
                max: 20
              }
            },
            {
              id: "kra4-d-tech",
              name: "Industry experience — Technical and skilled, per year",
              points: 3,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Service record or certificate of employment",
                "Brief job description"
              ],
              conditions: [
                "Newly appointed faculty only."
              ],
              groupMax: {
                group: "kra4-d",
                max: 20
              }
            },
            {
              id: "kra4-d-support",
              name: "Industry experience — Support or administrative staff, per year",
              points: 2,
              maxPoints: 20,
              contribution: "not-applicable",
              evidence: [
                "Service record or certificate of employment",
                "Brief job description"
              ],
              conditions: [
                "Newly appointed faculty only."
              ],
              groupMax: {
                group: "kra4-d",
                max: 20
              }
            }
          ]
        }
      ]
    }
  ],
  classification: [
    {
      priority: 1,
      kraId: "kra2",
      label: "KRA II — Research, Innovation and/or Creative Work",
      keywords: [
        "Journal",
        "ISSN",
        "Publications",
        "Patent",
        "Creative"
      ],
      fields: "Title, keywords, text"
    },
    {
      priority: 2,
      kraId: "kra1",
      label: "KRA I — Instruction",
      keywords: [
        "teaching",
        "course",
        "instruction",
        "module",
        "textbook"
      ],
      fields: "Title, keywords, text"
    },
    {
      priority: 3,
      kraId: "kra3",
      label: "KRA III — Extension",
      keywords: [
        "community",
        "outreach",
        "extension",
        "partnership"
      ],
      fields: "Title, keywords, text"
    },
    {
      priority: 4,
      kraId: "kra4",
      label: "KRA IV — Professional Development",
      keywords: [
        "training",
        "seminar",
        "certificate",
        "award"
      ],
      fields: "Title, keywords, text"
    }
  ],
  validationRules: [
    {
      condition: "Missing fields (title, author, or date)",
      action: "Invalid"
    },
    {
      condition: "Cannot classify",
      action: "Send to reviewer"
    },
    {
      condition: "Duplicate document (file hash)",
      action: "Ignore"
    }
  ],
  workflow: [
    "Faculty uploads document",
    "OCR / text extraction",
    "Classification (KRA → criterion → indicator)",
    "Indicator-specific evidence validation",
    "Scoring eligibility decision",
    "Automatic simulation score (complete + valid)",
    "Optional reviewer oversight",
    "Reviewer adjustment or invalidation",
    "Rank simulation recalculation"
  ]
};

FL.rules.findIndicator = function (id) {
  for (const kra of FL.rules.kras) {
    for (const criterion of kra.criteria) {
      for (const indicator of criterion.indicators) {
        if (indicator.id === id) return { kra, criterion, indicator };
      }
    }
  }
  return null;
};

FL.rules.findKra = function (id) {
  return FL.rules.kras.find(function (k) { return k.id === id; }) || null;
};

FL.rules.captureDefaults = function () {
  if (this._defaults) return;
  this._defaults = JSON.parse(JSON.stringify(this.kras));
};

FL.rules.scoreDraft = function () {
  const draft = { kras: {}, criteria: {}, indicators: {} };
  this.kras.forEach(function (kra) {
    draft.kras[kra.id] = { maxPoints: kra.maxPoints };
    kra.criteria.forEach(function (criterion) {
      draft.criteria[criterion.id] = { maxPoints: criterion.maxPoints };
      criterion.indicators.forEach(function (indicator) {
        const entry = { maxPoints: indicator.maxPoints };
        if (indicator.formula && indicator.formula.type === "rating") entry.multiplier = indicator.formula.multiplier;
        else if (typeof indicator.points === "number") entry.points = indicator.points;
        else return;
        draft.indicators[indicator.id] = entry;
      });
    });
  });
  return draft;
};

FL.rules.applySettings = function (settings) {
  this.captureDefaults();
  this.kras = JSON.parse(JSON.stringify(this._defaults));
  const saved = settings || {};
  const kras = saved.kras || {};
  const criteria = saved.criteria || {};
  const indicators = saved.indicators || {};
  this.kras.forEach(function (kra) {
    if (kras[kra.id] && typeof kras[kra.id].maxPoints === "number") kra.maxPoints = kras[kra.id].maxPoints;
    kra.criteria.forEach(function (criterion) {
      if (criteria[criterion.id] && typeof criteria[criterion.id].maxPoints === "number") {
        criterion.maxPoints = criteria[criterion.id].maxPoints;
      }
      criterion.indicators.forEach(function (indicator) {
        const update = indicators[indicator.id];
        if (update) {
          if (typeof update.maxPoints === "number") {
            indicator.maxPoints = update.maxPoints;
          }
          if (indicator.formula && indicator.formula.type === "rating" && typeof update.multiplier === "number") {
            indicator.formula.multiplier = update.multiplier;
          } else if (typeof update.points === "number") {
            indicator.points = update.points;
            if (!update.pointsLabel && indicator.pointsLabel && indicator.pointsLabel.indexOf("% contribution") === 0) {
              indicator.pointsLabel = "% contribution × " + update.points;
            }
          }
          if (typeof update.pointsLabel === "string" && update.pointsLabel.trim()) {
            indicator.pointsLabel = update.pointsLabel.trim();
          }
        }
        const meta = (saved.indicatorMeta || {})[indicator.id];
        if (!meta) return;
        if (typeof meta.name === "string" && meta.name.trim()) indicator.name = meta.name.trim();
        if (typeof meta.description === "string") indicator.description = meta.description.trim();
        if (typeof meta.formulaNote === "string") indicator.formulaNote = meta.formulaNote.trim();
        if (typeof meta.pointsLabel === "string" && meta.pointsLabel.trim()) {
          indicator.pointsLabel = meta.pointsLabel.trim();
        }
        if (Array.isArray(meta.evidence)) indicator.evidence = meta.evidence.slice();
        if (Array.isArray(meta.conditions)) indicator.conditions = meta.conditions.slice();
      });
    });
  });
};

FL.rules.buildSettingsFromRules = function () {
  const draft = this.scoreDraft();
  const store = window.FL && FL.store ? FL.store.kraSettings : null;
  if (store && store.indicatorMeta) draft.indicatorMeta = JSON.parse(JSON.stringify(store.indicatorMeta));
  return draft;
};
