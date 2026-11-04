import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// One UI group covering one or more official indicators (sole/co variants).
class Kra3AccomplishmentGroup {
  const Kra3AccomplishmentGroup({
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
      if (id.endsWith('-sole') || Kra3Catalog.contributionMode(id) == 'sole') return id;
    }
    return indicatorIds.length == 1 ? indicatorIds.first : null;
  }

  String? get coIndicatorId {
    for (final id in indicatorIds) {
      if (id.endsWith('-co') || Kra3Catalog.contributionMode(id) == 'declared') return id;
    }
    return null;
  }
}

/// KRA III indicator catalog (synced from backend `kra3_indicators.json`).
abstract final class Kra3Catalog {
  static const criterionA = 'kra3-a';
  static const criterionB = 'kra3-b';
  static const criterionC = 'kra3-c';
  static const criterionD = 'kra3-d';

  static List<Map<String, dynamic>> _indicators = const [];
  static bool _loaded = false;
  static Future<void>? _loadFuture;

  /// Call from `main()` so first KRA III screen does not wait on asset I/O.
  static Future<void> preload() => ensureLoaded();

  static Future<void> ensureLoaded() {
    if (_loaded) return Future.value();
    return _loadFuture ??= _loadFromAssets();
  }

  static Future<void> _loadFromAssets() async {
    final raw = await rootBundle.loadString('assets/kra3_indicators.json');
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
        return 'Service to the Institution';
      case criterionB:
        return 'Service to the Community';
      case criterionC:
        return 'Quality of Extension Services';
      case criterionD:
        return 'Administrative Designations';
      default:
        return 'KRA III';
    }
  }

  static String mainHubCardDescription(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Partnerships, networking, and income generation for the university';
      case criterionB:
        return 'Training, media, consultancy, and community extension work';
      case criterionC:
        return 'Client satisfaction ratings for extension projects';
      case criterionD:
        return 'Official administrative roles and designations';
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

  static List<Kra3AccomplishmentGroup> accomplishmentGroups(String criterionId) {
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
      return Kra3AccomplishmentGroup(
        key: key,
        title: meta.$1,
        description: meta.$2,
        icon: meta.$3,
        indicatorIds: ids,
      );
    }).toList();
  }

  static Kra3AccomplishmentGroup? groupByKey(String criterionId, String groupKey) {
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
    if (iid == 'kra3-a-linkage') return 'linkage';
    if (iid.contains('income')) return 'income';
    if (iid.startsWith('kra3-b-qa')) return 'accreditation';
    if (iid.startsWith('kra3-b-judge')) return 'judging';
    if (iid.startsWith('kra3-b-consult')) return 'consultancy';
    if (iid.contains('column')) return 'media_column';
    if (iid == 'kra3-b-host') return 'media_host';
    if (iid == 'kra3-b-guest') return 'media_guest';
    if (iid.startsWith('kra3-b-train')) return 'resource_person';
    if (iid.startsWith('kra3-b-ext')) return 'extension_project';
    if (iid == 'kra3-c-satisfaction') return 'csr';
    if (iid.startsWith('kra3-d-')) return 'designation';
    return 'generic_service';
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
      case 'linkage':
        return [
          'activityTitle',
          'organizationName',
          'facultyRole',
          'activityDate',
          'approvalReference',
        ];
      case 'income':
        return [
          'activityTitle',
          'organizationName',
          'facultyRole',
          'grossIncomeAmount',
          'activityDate',
        ];
      case 'accreditation':
      case 'judging':
      case 'consultancy':
      case 'extension_project':
        return [
          'activityTitle',
          'organizationName',
          'facultyRole',
          'serviceStartDate',
          'serviceEndDate',
        ];
      case 'media_column':
        return ['activityTitle', 'organizationName', 'activityDate'];
      case 'media_host':
        return [
          'activityTitle',
          'organizationName',
          'serviceStartDate',
          'serviceEndDate',
          'serviceDurationMonths',
        ];
      case 'media_guest':
        return ['activityTitle', 'organizationName', 'activityDate'];
      case 'resource_person':
        return [
          'activityTitle',
          'organizationName',
          'facultyRole',
          'activityDate',
          'deliveryHours',
        ];
      case 'csr':
        return ['activityTitle', 'csrOverallRating', 'linkedExtensionProjectId'];
      case 'designation':
        return [
          'designationTitle',
          'approvalReference',
          'serviceStartDate',
          'serviceEndDate',
          'serviceDurationMonths',
        ];
      default:
        return [
          'activityTitle',
          'organizationName',
          'facultyRole',
          'activityDate',
        ];
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

  /// Annex-aligned creative-work subfamily (mirrors backend `kra3_c_workflow.py`).
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
      case 'linkage':
        return 'Use a PDF that describes the partnership or MOA.';
      case 'income':
        return 'Use a PDF with certified income or financial evidence.';
      case 'csr':
        return 'Use the official CSR report PDF.';
      case 'designation':
        return 'Use your Special Order or designation document (PDF).';
      default:
        return 'Use a PDF that shows your extension service or activity.';
    }
  }

  static const _familyEvidenceSlots = <String, List<String>>{
    'linkage': [
      'partnership_approval',
      'moa_mou',
      'implementation_report',
      'faculty_initiative_certification',
    ],
    'income': ['primary_output', 'finance_certification', 'income_records'],
    'accreditation': [
      'primary_output',
      'official_appointment',
      'engagement_proof',
      'president_authorization',
    ],
    'judging': [
      'primary_output',
      'official_invitation',
      'competition_proof',
      'engagement_proof',
      'president_authorization',
    ],
    'consultancy': [
      'primary_output',
      'consultancy_agreement',
      'consultancy_report',
      'president_authorization',
    ],
    'media_column': ['primary_output', 'media_proof'],
    'media_host': ['primary_output', 'broadcast_schedule', 'media_proof'],
    'media_guest': ['primary_output', 'official_invitation', 'media_proof'],
    'resource_person': ['primary_output', 'official_invitation', 'engagement_proof'],
    'extension_project': ['primary_output', 'engagement_proof'],
    'csr': ['csr_report', 'csr_survey_instrument', 'linked_extension_project'],
    'designation': ['special_order_designation', 'primary_output'],
    'generic_service': ['primary_output', 'engagement_proof'],
  };

  static const _slotLabels = <String, String>{
    'primary_output': 'Primary evidence document',
    'partnership_approval': 'Board or executive approval for the partnership',
    'moa_mou': 'Notarized MOA or MOU (or project proposal)',
    'implementation_report': 'Implementation or terminal report',
    'faculty_initiative_certification': 'Certification that you initiated the partnership',
    'finance_certification': 'Finance Division certification of your contribution',
    'income_records': 'Financial reports or Sub-ARO equivalent',
    'official_appointment': 'Official appointment or designation letter',
    'engagement_proof': 'Proof of engagement (certificate, report, or travel order)',
    'president_authorization': 'President or Vice President authorization',
    'official_invitation': 'Official invitation letter',
    'competition_proof': 'Proof of award or competition',
    'consultancy_agreement': 'Consultancy agreement or contract',
    'consultancy_report': 'Consultancy certificate or terminal report',
    'media_proof': 'Published article, recording, or program proof',
    'broadcast_schedule': 'On-air schedule or hosting contract',
    'csr_report': 'Client Satisfaction Rating report',
    'csr_survey_instrument': 'Official CSR survey instrument',
    'linked_extension_project': 'Reference to eligible extension project',
    'special_order_designation': 'Special Order or official designation document',
  };

  /// Evidence slots required before faculty can send for review (matches backend Annex A checklists).
  static List<String> requiredEvidenceSlots(String indicatorId) {
    final fam = workflowFamily(indicatorId);
    return List<String>.from(
      _familyEvidenceSlots[fam] ?? _familyEvidenceSlots['generic_service']!,
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
