import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// One UI group covering one or more official indicators (sole/co variants).
class Kra4AccomplishmentGroup {
  const Kra4AccomplishmentGroup({
    required this.key,
    required this.title,
    required this.description,
    required this.icon,
    required this.indicatorIds,
  });

  final String key;
  final String title;
  final String description;
  final IconData icon;
  final List<String> indicatorIds;

  bool get needsAuthorshipChoice => indicatorIds.length > 1;

  String? get soleIndicatorId {
    for (final id in indicatorIds) {
      if (id.endsWith('-sole') || Kra4Catalog.contributionMode(id) == 'sole') return id;
    }
    return indicatorIds.length == 1 ? indicatorIds.first : null;
  }

  String? get coIndicatorId {
    for (final id in indicatorIds) {
      if (id.endsWith('-co') || Kra4Catalog.contributionMode(id) == 'declared') return id;
    }
    return null;
  }
}

/// KRA IV indicator catalog (synced from backend `kra4_indicators.json`).
abstract final class Kra4Catalog {
  static const criterionA = 'kra4-a';
  static const criterionB = 'kra4-b';
  static const criterionC = 'kra4-c';
  static const criterionD = 'kra4-d';

  static List<Map<String, dynamic>> _indicators = const [];
  static bool _loaded = false;
  static Future<void>? _loadFuture;

  /// Call from `main()` so first KRA IV screen does not wait on asset I/O.
  static Future<void> preload() => ensureLoaded();

  static Future<void> ensureLoaded() {
    if (_loaded) return Future.value();
    return _loadFuture ??= _loadFromAssets();
  }

  static Future<void> _loadFromAssets() async {
    final raw = await rootBundle.loadString('assets/kra4_indicators.json');
    final decoded = jsonDecode(raw);
    if (decoded is Map && decoded['indicators'] is List) {
      _indicators = (decoded['indicators'] as List)
          .whereType<Map>()
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
    }
    _loaded = true;
  }

  static List<Map<String, dynamic>> indicatorsFor(String criterionId) {
    final cid = criterionId.trim();
    return _indicators.where((r) => r['criterionId'] == cid).toList();
  }

  static Map<String, dynamic>? indicatorById(String? indicatorId) {
    final id = (indicatorId ?? '').trim();
    for (final row in _indicators) {
      if (row['id'] == id) return row;
    }
    return null;
  }

  static String mainHubCardTitle(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Professional organizations';
      case criterionB:
        return 'Education, training, and papers';
      case criterionC:
        return 'Awards and recognition';
      case criterionD:
        return 'Previous relevant experience';
      default:
        return 'KRA IV';
    }
  }

  static String mainHubCardDescription(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Membership and active participation in a registered professional organization';
      case criterionB:
        return 'Degrees, seminars, trainings, and conference presentations';
      case criterionC:
        return 'Institutional, local, national, and international awards';
      case criterionD:
        return 'Qualifying years in prior relevant roles (bonus points)';
      default:
        return '';
    }
  }

  static String criterionBadge(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Criterion A';
      case criterionB:
        return 'Criterion B';
      case criterionC:
        return 'Criterion C';
      case criterionD:
        return 'Criterion D';
      default:
        return '';
    }
  }

  static String criterionTitle(String criterionId) => mainHubCardTitle(criterionId);

  static String criterionHubSubtitle(String criterionId) {
    return 'What would you like to add?';
  }

  static IconData criterionIcon(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return Icons.apartment_outlined;
      case criterionB:
        return Icons.groups_outlined;
      case criterionC:
        return Icons.star_outline;
      case criterionD:
        return Icons.badge_outlined;
      default:
        return Icons.folder_outlined;
    }
  }

  static Color criterionIconBackground(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return const Color(0xFFE8F0FE);
      case criterionB:
        return const Color(0xFFFFF4E5);
      case criterionC:
        return const Color(0xFFECFDF5);
      case criterionD:
        return const Color(0xFFF3E8FF);
      default:
        return const Color(0xFFEEF2F6);
    }
  }

  /// Stable group key for UI clustering (does not change official indicator IDs).
  static String groupKeyForIndicator(String indicatorId) {
    final parts = indicatorId.split('-');
    if (parts.length < 3) return indicatorId;
    final tail = parts.sublist(2);
    if (tail.isNotEmpty && (tail.last == 'sole' || tail.last == 'co')) {
      tail.removeLast();
    }
    return tail.join('-');
  }

  static List<Kra4AccomplishmentGroup> accomplishmentGroups(String criterionId) {
    final rows = indicatorsFor(criterionId);
    final byKey = <String, List<String>>{};
    for (final row in rows) {
      final id = row['id']?.toString() ?? '';
      if (id.isEmpty) continue;
      final key = groupKeyForIndicator(id);
      byKey.putIfAbsent(key, () => []).add(id);
    }
    final keys = byKey.keys.toList()..sort(_groupSortOrder);
    return keys.map((key) {
      final ids = byKey[key]!..sort();
      final meta = _groupMeta(key, criterionId);
      return Kra4AccomplishmentGroup(
        key: key,
        title: meta.$1,
        description: meta.$2,
        icon: meta.$3,
        indicatorIds: ids,
      );
    }).toList();
  }

  static Kra4AccomplishmentGroup? groupByKey(String criterionId, String groupKey) {
    for (final g in accomplishmentGroups(criterionId)) {
      if (g.key == groupKey) return g;
    }
    return null;
  }

  static int _groupSortOrder(String a, String b) {
    const order = [
      'book',
      'chapter',
      'journal',
      'monograph',
      'translation',
      'cite',
      'patent-a',
      'patent-p',
      'patent-g',
      'comm-local',
      'comm-intl',
      'um',
      'id',
      'sw-new',
      'sw-upd',
      'variety',
    ];
    final ia = order.indexOf(a);
    final ib = order.indexOf(b);
    if (ia >= 0 && ib >= 0) return ia.compareTo(ib);
    if (ia >= 0) return -1;
    if (ib >= 0) return 1;
    return a.compareTo(b);
  }

  static (String, String, IconData) _groupMeta(String key, String criterionId) {
    const meta = <String, (String, String, IconData)>{
      'book': ('Book', 'A book you wrote or co-wrote.', Icons.auto_stories_outlined),
      'chapter': ('Book chapter', 'A chapter in an edited academic book.', Icons.library_books_outlined),
      'journal': ('Journal article', 'A research paper published in a journal.', Icons.article_outlined),
      'monograph': ('Monograph', 'A scholarly monograph you authored.', Icons.menu_book),
      'translation': ('Translation', 'A translated academic work.', Icons.translate),
      'cite': ('Citation received', 'Your work was cited by another publication.', Icons.format_quote),
      'patent-a': ('Patent application', 'Your invention was accepted or filed with the patent office.', Icons.gavel_outlined),
      'patent-p': ('Patent publication', 'Your patent application was published.', Icons.hourglass_top_outlined),
      'patent-g': ('Patent certificate', 'Your patent was granted.', Icons.verified_outlined),
      'comm-local': ('Commercialization (local)', 'Your invention was commercialized locally.', Icons.storefront_outlined),
      'comm-intl': ('Commercialization (international)', 'Your invention was commercialized abroad.', Icons.public_outlined),
      'um': ('Utility model', 'A registered utility model.', Icons.build_outlined),
      'id': ('Industrial design', 'A registered industrial design.', Icons.design_services_outlined),
      'sw-new': ('New software / algorithm', 'Original software or algorithm you developed.', Icons.code_outlined),
      'sw-upd': ('Updated software / algorithm', 'A major update to software or an algorithm.', Icons.system_update_alt_outlined),
      'variety': ('New plant variety', 'A registered new plant variety.', Icons.eco_outlined),
      'music-comp': ('Musical composition', 'An original musical composition.', Icons.music_note_outlined),
      'music-arr': ('Musical arrangement', 'An arrangement of music you created.', Icons.queue_music_outlined),
      'music-perf': ('Musical performance', 'A documented musical performance.', Icons.piano_outlined),
      'conducting': ('Conducting', 'Conducting a musical performance.', Icons.leaderboard_outlined),
      'music-prod': ('Music production', 'Producing a musical recording or work.', Icons.album_outlined),
      'choreo': ('Choreography', 'Original dance choreography.', Icons.directions_run_outlined),
      'dance-perf': ('Dance performance', 'A documented dance performance.', Icons.accessibility_new_outlined),
      'playwright': ('Play / script', 'A play or theatrical script you wrote.', Icons.theater_comedy_outlined),
      'directing': ('Stage or film directing', 'Directing a stage or film production.', Icons.movie_creation_outlined),
      'acting': ('Acting performance', 'A lead or supporting acting performance.', Icons.person_outline),
      'prod-design': ('Production design', 'Design for stage, film, or media production.', Icons.palette_outlined),
      'visual': ('Visual artwork', 'Visual art such as painting or sculpture.', Icons.brush_outlined),
      'arch-design': ('Architectural design', 'An architectural or built-environment design.', Icons.architecture_outlined),
      'film': ('Film or audiovisual work', 'A film or audiovisual creative work.', Icons.videocam_outlined),
      'novel': ('Novel or long fiction', 'A novel or long-form literary work.', Icons.import_contacts_outlined),
      'story': ('Short story', 'A published short story.', Icons.short_text_outlined),
      'poetry': ('Poetry', 'Published poetry.', Icons.format_italic_outlined),
      'essay': ('Essay or literary work', 'An essay or similar literary contribution.', Icons.description_outlined),
    };
    final hit = meta[key];
    if (hit != null) return hit;
    String? sampleId;
    for (final row in indicatorsFor(criterionId)) {
      if (groupKeyForIndicator(row['id']?.toString() ?? '') == key) {
        sampleId = row['id']?.toString();
        break;
      }
    }
    final sample = indicatorById(sampleId);
    final name = (sample?['name'] ?? key).toString();
    return (name, userFacingSummary(sampleId ?? ''), Icons.task_outlined);
  }

  static String workflowFamily(String indicatorId) {
    final iid = indicatorId.trim();
    if (iid.startsWith('kra4-a-')) return 'organization';
    if (iid.startsWith('kra4-b-post') ||
        iid.startsWith('kra4-b-master') ||
        iid == 'kra4-b-doctorate') {
      return 'education';
    }
    if (iid.startsWith('kra4-b-part')) return 'capacity_building';
    if (iid.startsWith('kra4-b-paper')) return 'paper_presentation';
    if (iid.startsWith('kra4-c-')) return 'award';
    if (iid.startsWith('kra4-d-')) return 'prior_experience';
    return 'generic';
  }

  static String contributionMode(String indicatorId) {
    final row = indicatorById(indicatorId);
    final c = (row?['contribution'] ?? '').toString().trim().toLowerCase();
    if (c == 'declared' || c == 'sole' || c == 'not-applicable') return c;
    final parts = indicatorId.split('-');
    if (parts.isNotEmpty && parts.last == 'co') return 'declared';
    if (parts.isNotEmpty && parts.last == 'sole') return 'sole';
    return 'not-applicable';
  }

  static List<String> metadataFieldIds(String indicatorId) {
    switch (workflowFamily(indicatorId)) {
      case 'organization':
        return [
          'activityTitle',
          'organizationName',
          'facultyRole',
          'serviceStartDate',
          'serviceEndDate',
        ];
      case 'education':
        return ['degreeTitle', 'institutionName', 'activityDate'];
      case 'capacity_building':
        return [
          'eventTitle',
          'organizationName',
          'eventDurationHours',
          'eventScope',
          'activityDate',
          'approvalReference',
        ];
      case 'paper_presentation':
        return [
          'paperTitle',
          'eventTitle',
          'organizationName',
          'eventScope',
          'activityDate',
          'approvalReference',
        ];
      case 'award':
        return ['awardTitle', 'awardLevel', 'organizationName', 'activityDate'];
      case 'prior_experience':
        return [
          'employerName',
          'positionTitle',
          'serviceStartDate',
          'serviceEndDate',
          'experienceYears',
        ];
      default:
        return ['activityTitle', 'organizationName', 'activityDate'];
    }
  }

  static String metadataLabel(String fieldId, [String? indicatorId]) {
    if (indicatorId != null && indicatorId.isNotEmpty) {
      return metadataLabelForIndicator(fieldId, indicatorId);
    }
    return _genericMetadataLabel(fieldId);
  }

  static String _criterionAPublicationKind(String indicatorId) {
    if (indicatorId.contains('book')) return 'book';
    if (indicatorId.contains('chapter')) return 'chapter';
    if (indicatorId.contains('journal')) return 'journal';
    if (indicatorId.contains('monograph')) return 'monograph';
    if (indicatorId.contains('translation')) return 'translation';
    if (indicatorId.contains('cite')) return 'cite';
    return 'publication';
  }

  static bool _isPerformanceIndicator(String indicatorId) =>
      workflowFamily(indicatorId) == 'performance_work';

  /// Annex-aligned creative-work subfamily (mirrors backend `kra4_c_workflow.py`).
  static String criterionCSubfamily(String indicatorId) {
    final iid = indicatorId.trim();
    if (!iid.startsWith('$criterionC-')) return 'literary';
    if (iid.startsWith('$criterionC-music-comp-') || iid.startsWith('$criterionC-music-arr-')) {
      return 'music_composition';
    }
    if (iid.startsWith('$criterionC-music-prod-')) return 'music_production';
    if (iid.startsWith('$criterionC-music-perf') || iid.startsWith('$criterionC-conducting')) {
      return 'music_performance';
    }
    if (iid.startsWith('$criterionC-choreo-')) return 'dance_choreography';
    if (iid.startsWith('$criterionC-dance-perf')) return 'dance_performance';
    if (iid.startsWith('$criterionC-directing') || iid.startsWith('$criterionC-acting')) {
      return 'theater_performance';
    }
    if (iid.startsWith('$criterionC-playwright-') || iid.startsWith('$criterionC-prod-design')) {
      return 'theater';
    }
    if (iid.startsWith('$criterionC-visual')) return 'visual_arts';
    if (iid.startsWith('$criterionC-arch-design')) return 'design_exhibition';
    if (iid.startsWith('$criterionC-film')) return 'film';
    if (iid.startsWith('$criterionC-novel-') ||
        iid.startsWith('$criterionC-story-') ||
        iid.startsWith('$criterionC-poetry') ||
        iid.startsWith('$criterionC-essay')) {
      return 'literary';
    }
    return 'literary';
  }

  static String? _criterionCMetadataLabel(String fieldId, String indicatorId) {
    const profiles = <String, Map<String, String>>{
      'music_composition': {
        'outputTitle': 'Title of composition or arrangement',
        'authorsLine': 'Composer or arranger',
        'outputVenue': 'Venue, organizer, or publisher',
        'publicationDate': 'Date of first performance or publication',
      },
      'music_production': {
        'outputTitle': 'Title of produced work',
        'authorsLine': 'Producer or creator',
        'outputVenue': 'Label, platform, or release venue',
        'publicationDate': 'Release or publication date',
      },
      'music_performance': {
        'outputTitle': 'Title of performance',
        'authorsLine': 'Performer or conductor',
        'outputVenue': 'Performance venue or organizer',
        'publicationDate': 'Date of performance',
      },
      'dance_choreography': {
        'outputTitle': 'Title of choreography',
        'authorsLine': 'Choreographer',
        'outputVenue': 'Venue or organizer',
        'publicationDate': 'Date of first performance',
      },
      'dance_performance': {
        'outputTitle': 'Title of dance performance',
        'authorsLine': 'Dancer or performer',
        'outputVenue': 'Performance venue or organizer',
        'publicationDate': 'Date of performance',
      },
      'theater': {
        'outputTitle': 'Title of production or role',
        'authorsLine': 'Playwright or creator',
        'outputVenue': 'Theater, organizer, or festival',
        'publicationDate': 'Date of production or publication',
      },
      'theater_performance': {
        'outputTitle': 'Title of performance',
        'authorsLine': 'Performer or director',
        'outputVenue': 'Performance venue or organizer',
        'publicationDate': 'Date of performance',
      },
      'visual_arts': {
        'outputTitle': 'Title of artwork',
        'authorsLine': 'Artist or creator',
        'outputVenue': 'Gallery or exhibition venue',
        'publicationDate': 'Exhibition date',
      },
      'design_exhibition': {
        'outputTitle': 'Title of design or project',
        'authorsLine': 'Designer or creator',
        'outputVenue': 'Exhibition, competition, or organizer',
        'publicationDate': 'Exhibition or competition date',
      },
      'film': {
        'outputTitle': 'Film title',
        'authorsLine': 'Director or creator',
        'outputVenue': 'Festival, venue, or organizer',
        'publicationDate': 'Screening or release date',
      },
      'literary': {
        'outputTitle': 'Title of literary work',
        'authorsLine': 'Author or contributor',
        'outputVenue': 'Publisher or publication',
        'publicationDate': 'Publication date',
      },
    };
    final sub = criterionCSubfamily(indicatorId);
    if (fieldId == 'declaredContributionPercent') {
      return 'Your verified contribution (%)';
    }
    return profiles[sub]?[fieldId];
  }

  static String metadataLabelForIndicator(String fieldId, String indicatorId) {
    return _genericMetadataLabel(fieldId);
  }

  static String _genericMetadataLabel(String fieldId) {
    switch (fieldId) {
      case 'activityTitle':
        return 'Activity or project name';
      case 'organizationName':
        return 'Organization or partner';
      case 'facultyRole':
        return 'Your role';
      case 'activityDate':
        return 'Date';
      case 'approvalReference':
        return 'Approval or Special Order reference';
      case 'grossIncomeAmount':
        return 'Gross income amount (₱)';
      case 'deliveryHours':
        return 'Eligible service hours';
      case 'csrOverallRating':
        return 'Overall satisfaction rating (0–100)';
      case 'linkedExtensionProjectId':
        return 'Linked extension project';
      case 'designationTitle':
        return 'Administrative designation';
      case 'serviceStartDate':
        return 'Start date';
      case 'serviceEndDate':
        return 'End date';
      case 'serviceDurationMonths':
        return 'Months of service';
      case 'institutionName':
        return 'School or institution';
      case 'degreeTitle':
        return 'Degree or qualification';
      case 'eventTitle':
        return 'Event or training name';
      case 'eventDurationHours':
        return 'Total hours';
      case 'eventScope':
        return 'Local or international';
      case 'paperTitle':
        return 'Paper title';
      case 'awardTitle':
        return 'Award name';
      case 'awardLevel':
        return 'Award level';
      case 'employerName':
        return 'Employer';
      case 'positionTitle':
        return 'Position or role';
      case 'experienceYears':
        return 'Qualifying years';
      case 'outputTitle':
        return 'Title';
      case 'authorsLine':
        return 'Names';
      case 'outputVenue':
        return 'Journal or venue';
      case 'publicationDate':
        return 'Date';
      case 'publicationReference':
        return 'DOI (optional)';
      case 'registrationNumber':
        return 'Registration number';
      case 'registrationDate':
        return 'Registration date';
      case 'citationContext':
        return 'Citation details';
      case 'declaredContributionPercent':
        return 'Your share (%)';
      default:
        return fieldId.replaceAll(RegExp(r'([A-Z])'), ' ').trim();
    }
  }

  /// Plain name for lists (not raw upload filenames).
  static String accomplishmentGroupTitle(String indicatorId) {
    final id = indicatorId.trim();
    if (id.isEmpty) return 'Your accomplishment';
    final crit = indicatorById(id)?['criterionId']?.toString() ?? criterionA;
    return _groupMeta(groupKeyForIndicator(id), crit).$1;
  }

  static String friendlyUploadTitle(String indicatorId) {
    return accomplishmentGroupTitle(indicatorId);
  }

  static String submissionListTitle({
    required String? indicatorId,
    String? outputTitle,
  }) {
    final type = accomplishmentGroupTitle(indicatorId ?? '');
    final raw = (outputTitle ?? '').trim();
    if (raw.isEmpty || _looksLikeUploadFilename(raw) || _looksLikePlaceholderTitle(raw, indicatorId)) {
      return type;
    }
    return raw;
  }

  static bool _looksLikeUploadFilename(String value) {
    final t = value.trim();
    if (t.isEmpty) return false;
    if (RegExp(r'^KRA2[_\-]', caseSensitive: false).hasMatch(t)) return true;
    if (RegExp(r'\.pdf$', caseSensitive: false).hasMatch(t)) return true;
    if (RegExp(r'_\d{2}_', caseSensitive: false).hasMatch(t) && t.contains('_')) return true;
    return false;
  }

  static bool _looksLikePlaceholderTitle(String raw, String? indicatorId) {
    if (indicatorId == null || indicatorId.isEmpty) return false;
    final lower = raw.toLowerCase();
    if (lower == userFacingTitle(indicatorId).toLowerCase()) return true;
    if (lower == accomplishmentGroupTitle(indicatorId).toLowerCase()) return true;
    final row = indicatorById(indicatorId);
    final name = (row?['name'] ?? '').toString().toLowerCase();
    return name.isNotEmpty && lower == name;
  }

  /// Advisory hint when filename suggests a different accomplishment type than selected.
  static String? documentTypeMismatchHint(String indicatorId, String fileName) {
    final name = fileName.toLowerCase();
    if (name.isEmpty) return null;
    final key = groupKeyForIndicator(indicatorId);
    final mentionsGrant = name.contains('grant') || name.contains('certificate');
    final mentionsAccept = name.contains('accept');
    final mentionsPublication = name.contains('publication');
    final mentionsApplication = name.contains('application') || name.contains('filed');

    if (key == 'patent-a' && mentionsGrant && !mentionsAccept) {
      return 'This file looks like a patent certificate. You chose a patent application. Go back and pick "Patent certificate" if that is correct.';
    }
    if (key == 'patent-g' && mentionsAccept && !mentionsGrant) {
      return 'This file looks like an acceptance notice, not a grant certificate. Check that you picked the right accomplishment type.';
    }
    if (key == 'patent-a' && mentionsPublication && !mentionsApplication) {
      return 'This file looks like a publication notice. You may need "Patent publication" instead of "Patent application".';
    }
    if (key == 'patent-p' && mentionsGrant) {
      return 'This file looks like a grant certificate. You chose patent publication — pick "Patent certificate" if the patent was granted.';
    }
    return null;
  }

  static String primaryUploadLabel(String indicatorId) {
    switch (workflowFamily(indicatorId)) {
      case 'organization':
        return 'Use a PDF membership certificate or organization ID.';
      case 'education':
        return 'Use a PDF diploma, certificate, or certified transcript.';
      case 'capacity_building':
        return 'Use a PDF certificate of participation or training proof.';
      case 'paper_presentation':
        return 'Use a PDF acceptance letter or presenter certificate.';
      case 'award':
        return 'Use a PDF award certificate or official award notice.';
      case 'prior_experience':
        return 'Use a PDF service record or certificate of employment.';
      default:
        return 'Use a clear PDF that supports this accomplishment.';
    }
  }

  static const _familyEvidenceSlots = <String, List<String>>{
    'organization': ['membership_proof', 'organization_profile', 'participation_proof'],
    'education': ['diploma_or_certificate', 'certified_transcript'],
    'capacity_building': ['participation_certificate', 'event_program', 'approval_evidence'],
    'paper_presentation': [
      'acceptance_letter',
      'presentation_certificate',
      'approval_evidence',
      'event_program',
    ],
    'award': ['award_certificate', 'award_criteria', 'awarding_org_profile'],
    'prior_experience': ['employment_record', 'position_description'],
    'generic': ['primary_output', 'participation_proof'],
  };

  static const _slotLabels = <String, String>{
    'primary_output': 'Primary evidence document',
    'membership_proof': 'Membership certificate or ID',
    'organization_profile': 'Organization registration or profile',
    'participation_proof': 'Evidence of active participation',
    'diploma_or_certificate': 'Diploma or certificate',
    'certified_transcript': 'Certified transcript or TOR',
    'participation_certificate': 'Certificate of participation',
    'event_program': 'Event program or agenda',
    'approval_evidence': 'Official approval (when required)',
    'acceptance_letter': 'Letter or certificate of acceptance',
    'presentation_certificate': 'Presenter certificate',
    'award_certificate': 'Award certificate or photo of award',
    'award_criteria': 'Award criteria and selection process',
    'awarding_org_profile': 'Awarding organization profile',
    'employment_record': 'Service record or certificate of employment',
    'position_description': 'Position description or appointment',
  };

  /// Evidence slots required before faculty can send for review (matches backend Annex A checklists).
  static List<String> requiredEvidenceSlots(String indicatorId) {
    final fam = workflowFamily(indicatorId);
    return List<String>.from(
      _familyEvidenceSlots[fam] ?? _familyEvidenceSlots['generic']!,
    );
  }

  static String slotLabelForIndicator(String slotId, String indicatorId) {
    return _slotLabels[slotId] ?? slotId.replaceAll('_', ' ');
  }

  static String slotLabel(String slotId) => slotLabelForIndicator(slotId, '');

  static String facultySlotStatusSubtitle(String slotId, Map<String, dynamic>? checklistEntry) {
    final entry = checklistEntry;
    if (entry == null) {
      return 'Not uploaded yet';
    }
    final docId = entry['documentId']?.toString().trim() ?? '';
    final status = (entry['status'] ?? 'missing').toString().toLowerCase();
    if (docId.isEmpty || status == 'missing') {
      return 'Not uploaded yet';
    }
    if (status == 'verified') {
      return 'Uploaded and verified by reviewer';
    }
    return 'Uploaded — your reviewer will verify this';
  }

  static bool requiresContributionCertificate(String indicatorId) {
    return contributionMode(indicatorId) == 'declared';
  }

  static String userFacingTitle(String indicatorId) {
    return (indicatorById(indicatorId)?['name'] ?? indicatorId).toString();
  }

  static String userFacingSummary(String indicatorId) {
    final hints = indicatorById(indicatorId)?['evidenceHints'];
    if (hints is List && hints.isNotEmpty) {
      return hints.first.toString();
    }
    return primaryUploadLabel(indicatorId);
  }
}
