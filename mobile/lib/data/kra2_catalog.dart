import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// One UI group covering one or more official indicators (sole/co variants).
class Kra2AccomplishmentGroup {
  const Kra2AccomplishmentGroup({
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
      if (id.endsWith('-sole') || Kra2Catalog.contributionMode(id) == 'sole') return id;
    }
    return indicatorIds.length == 1 ? indicatorIds.first : null;
  }

  String? get coIndicatorId {
    for (final id in indicatorIds) {
      if (id.endsWith('-co') || Kra2Catalog.contributionMode(id) == 'declared') return id;
    }
    return null;
  }
}

/// KRA II indicator catalog (synced from backend `kra2_indicators.json`).
abstract final class Kra2Catalog {
  static const criterionA = 'kra2-a';
  static const criterionB = 'kra2-b';
  static const criterionC = 'kra2-c';

  static List<Map<String, dynamic>> _indicators = const [];
  static bool _loaded = false;
  static Future<void>? _loadFuture;

  /// Call from `main()` so first KRA II screen does not wait on asset I/O.
  static Future<void> preload() => ensureLoaded();

  static Future<void> ensureLoaded() {
    if (_loaded) return Future.value();
    return _loadFuture ??= _loadFromAssets();
  }

  static Future<void> _loadFromAssets() async {
    final raw = await rootBundle.loadString('assets/kra2_indicators.json');
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
        return 'Publications';
      case criterionB:
        return 'Inventions';
      case criterionC:
        return 'Creative Works & Research Impact';
      default:
        return 'KRA II';
    }
  }

  static String mainHubCardDescription(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'Books, research papers, and journal articles';
      case criterionB:
        return 'Patents, new ideas, and useful inventions';
      case criterionC:
        return 'Creative works, performances, and other recognized research contributions';
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
      default:
        return '';
    }
  }

  static String criterionTitle(String criterionId) {
    return mainHubCardTitle(criterionId);
  }

  static String criterionHubSubtitle(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return 'What would you like to add?';
      case criterionB:
        return 'What would you like to add?';
      case criterionC:
        return 'What would you like to add?';
      default:
        return 'Choose an accomplishment type to begin';
    }
  }

  static IconData criterionIcon(String criterionId) {
    switch (criterionId) {
      case criterionA:
        return Icons.menu_book_outlined;
      case criterionB:
        return Icons.lightbulb_outline;
      case criterionC:
        return Icons.emoji_events_outlined;
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

  static List<Kra2AccomplishmentGroup> accomplishmentGroups(String criterionId) {
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
      return Kra2AccomplishmentGroup(
        key: key,
        title: meta.$1,
        description: meta.$2,
        icon: meta.$3,
        indicatorIds: ids,
      );
    }).toList();
  }

  static Kra2AccomplishmentGroup? groupByKey(String criterionId, String groupKey) {
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
    final parts = indicatorId.split('-');
    final familyToken = parts.length >= 3 ? parts[2] : '';
    final crit = parts.length >= 2 ? '${parts[0]}-${parts[1]}' : '';
    if (familyToken == 'cite') return 'citation_impact';
    if (crit == criterionB) {
      if (familyToken.startsWith('comm')) return 'commercialization';
      return 'invention_ip';
    }
    if (crit == criterionC) {
      const perf = {'music-perf', 'dance-perf', 'conducting', 'acting', 'directing'};
      if (perf.contains(familyToken) || indicatorId.contains('-perf')) {
        return 'performance_work';
      }
      return 'creative_work';
    }
    return 'publication_output';
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
    final family = workflowFamily(indicatorId);
    const base = ['outputTitle', 'authorsLine', 'outputVenue', 'publicationDate'];
    if (family == 'citation_impact') {
      return ['outputTitle', 'citationContext', 'publicationDate'];
    }
    if (family == 'invention_ip') {
      final fields = [
        'outputTitle',
        'registrationNumber',
        'registrationDate',
        'authorsLine',
        'outputVenue',
      ];
      if (contributionMode(indicatorId) == 'declared') {
        fields.add('declaredContributionPercent');
      }
      return fields;
    }
    if (family == 'commercialization') {
      return ['outputTitle', 'outputVenue', 'publicationDate', 'authorsLine'];
    }
    if (contributionMode(indicatorId) == 'declared') {
      return [...base, 'declaredContributionPercent'];
    }
    return base;
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

  /// Annex-aligned creative-work subfamily (mirrors backend `kra2_c_workflow.py`).
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
    if (indicatorId.startsWith('$criterionC-')) {
      return _criterionCMetadataLabel(fieldId, indicatorId) ?? _genericMetadataLabel(fieldId);
    }
    final family = workflowFamily(indicatorId);
    final critAKind =
        indicatorId.startsWith('$criterionA-') ? _criterionAPublicationKind(indicatorId) : '';
    switch (fieldId) {
      case 'outputTitle':
        if (family == 'invention_ip') return 'Name of your invention';
        if (family == 'citation_impact') return 'Title of your published work';
        if (family == 'performance_work') return 'Title of performance';
        if (family == 'creative_work') {
          return 'Title of your work';
        }
        if (critAKind == 'book' || critAKind == 'monograph') return 'Title of your book';
        if (critAKind == 'chapter') return 'Title of your chapter';
        if (critAKind == 'translation') return 'Title of your research output';
        return 'Title of your article';
      case 'authorsLine':
        if (family == 'invention_ip') return 'Inventor names';
        if (family == 'performance_work') return 'Performer / creator';
        if (family == 'creative_work') {
          return 'Creator names';
        }
        return 'Author names';
      case 'outputVenue':
        if (_isPerformanceIndicator(indicatorId)) {
          return 'Performance venue or organizer';
        }
        if (family == 'invention_ip') return 'Patent office or registry';
        if (family == 'commercialization') return 'Company or market';
        if (critAKind == 'book' || critAKind == 'chapter' || critAKind == 'monograph') {
          return 'Publisher';
        }
        if (critAKind == 'translation') return 'Organization or program';
        if (critAKind == 'journal') return 'Journal name';
        return 'Journal or publisher';
      case 'publicationDate':
        if (family == 'invention_ip') return 'Patent date';
        if (family == 'performance_work') return 'Date of performance';
        if (family == 'creative_work') {
          return 'Date of the work';
        }
        if (critAKind == 'translation') return 'Date of utilization or completion';
        return 'Publication date';
      case 'publicationReference':
        if (critAKind == 'book' ||
            critAKind == 'chapter' ||
            critAKind == 'monograph' ||
            critAKind == 'translation') {
          return 'ISBN or reference number (optional)';
        }
        if (critAKind == 'journal') return 'DOI (if you have one)';
        return 'Reference number (optional)';
      case 'registrationNumber':
        return 'Patent or registration number';
      case 'registrationDate':
        return 'Filing or registration date';
      case 'citationContext':
        return 'Where your work was cited';
      case 'declaredContributionPercent':
        return 'Your share of the work (%)';
      default:
        return _genericMetadataLabel(fieldId);
    }
  }

  static String _genericMetadataLabel(String fieldId) {
    switch (fieldId) {
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
      case 'invention_ip':
        return 'Use a PDF from the patent office that matches this accomplishment.';
      case 'citation_impact':
        return 'Use a PDF that shows your work was cited.';
      case 'commercialization':
        return 'Use a PDF that shows your invention was commercialized.';
      case 'creative_work':
      case 'performance_work':
        return 'Use a PDF that shows your creative or performance work.';
      default:
        return 'Use a PDF of your published article or book.';
    }
  }

  /// Evidence slots required before faculty can send for review (matches backend Annex A checklists).
  static List<String> requiredEvidenceSlots(String indicatorId) {
    final id = indicatorId.trim();
    if (id.startsWith('$criterionA-')) {
      const criterionASlots = {
        'kra2-a-book-sole': ['primary_output', 'peer_review_evidence'],
        'kra2-a-book-co': ['primary_output', 'contribution_certificate'],
        'kra2-a-chapter-sole': ['primary_output', 'peer_review_evidence'],
        'kra2-a-chapter-co': ['primary_output', 'contribution_certificate'],
        'kra2-a-journal-sole': ['primary_output', 'indexing_certification'],
        'kra2-a-journal-co': [
          'primary_output',
          'indexing_certification',
          'contribution_certificate',
        ],
        'kra2-a-monograph-sole': ['primary_output', 'peer_review_evidence'],
        'kra2-a-monograph-co': ['primary_output', 'contribution_certificate'],
        'kra2-a-translation-sole': ['primary_output', 'translation_impact_evidence'],
        'kra2-a-translation-co': [
          'primary_output',
          'translation_impact_evidence',
          'contribution_certificate',
        ],
        'kra2-a-cite': [
          'primary_output',
          'citing_publication_evidence',
          'indexing_certification',
        ],
      };
      return List<String>.from(criterionASlots[id] ?? ['primary_output']);
    }
    if (id.startsWith('$criterionB-')) {
      const criterionBSlots = {
        'kra2-b-patent-a-sole': ['primary_output', 'invention_photo', 'president_special_order'],
        'kra2-b-patent-p-sole': ['primary_output', 'invention_photo', 'president_special_order'],
        'kra2-b-patent-g-sole': ['primary_output', 'invention_photo', 'president_special_order'],
        'kra2-b-patent-a-co': ['primary_output', 'contribution_certificate'],
        'kra2-b-patent-p-co': ['primary_output', 'contribution_certificate'],
        'kra2-b-patent-g-co': ['primary_output', 'contribution_certificate'],
        'kra2-b-comm-local': [
          'product_photo',
          'patent_certificate',
          'licensing_or_cpr_evidence',
          'commercialization_proof',
          'rd_itso_certification',
        ],
        'kra2-b-comm-intl': [
          'product_photo',
          'patent_certificate',
          'licensing_or_cpr_evidence',
          'commercialization_proof',
          'rd_itso_certification',
        ],
        'kra2-b-um-sole': ['primary_output', 'invention_photo', 'president_special_order'],
        'kra2-b-id-sole': ['primary_output', 'invention_photo', 'president_special_order'],
        'kra2-b-um-co': ['primary_output', 'contribution_certificate'],
        'kra2-b-id-co': ['primary_output', 'contribution_certificate'],
        'kra2-b-sw-new-sole': [
          'president_special_order',
          'project_summary',
          'software_documentation',
          'primary_output',
          'utilization_certification',
        ],
        'kra2-b-sw-new-co': [
          'president_special_order',
          'project_summary',
          'software_documentation',
          'primary_output',
          'utilization_certification',
          'contribution_certificate',
        ],
        'kra2-b-sw-upd-sole': [
          'president_special_order',
          'project_summary',
          'primary_output',
          'utilization_certification',
          'software_update_description',
        ],
        'kra2-b-sw-upd-co': [
          'president_special_order',
          'project_summary',
          'primary_output',
          'utilization_certification',
          'software_update_description',
          'contribution_certificate',
        ],
        'kra2-b-variety-sole': ['president_special_order', 'registration_deposit_evidence'],
        'kra2-b-variety-co': ['registration_deposit_evidence', 'contribution_certificate'],
      };
      return List<String>.from(criterionBSlots[id] ?? ['primary_output']);
    }
    if (id.startsWith('$criterionC-')) {
      const criterionCSlots = {
        'kra2-c-acting': ['primary_output', 'program_documentation', 'media_documentation', 'role_certification'],
        'kra2-c-arch-design': ['primary_output', 'invitation_acceptance', 'exhibition_documentation', 'authorship_documentation', 'organizing_body_info'],
        'kra2-c-choreo-co': ['primary_output', 'contribution_certificate'],
        'kra2-c-choreo-sole': ['primary_output', 'invitation_acceptance', 'performance_proof', 'role_certification'],
        'kra2-c-conducting': ['primary_output', 'invitation_acceptance', 'role_certification'],
        'kra2-c-dance-perf': ['primary_output', 'role_certification'],
        'kra2-c-directing': ['primary_output', 'program_documentation', 'media_documentation', 'role_certification'],
        'kra2-c-essay': ['primary_output', 'editorial_review', 'publisher_credibility'],
        'kra2-c-film': ['primary_output', 'invitation_acceptance', 'festival_program', 'role_certification'],
        'kra2-c-music-arr-co': ['primary_output', 'contribution_certificate'],
        'kra2-c-music-arr-sole': ['primary_output', 'invitation_acceptance', 'performance_proof', 'role_certification'],
        'kra2-c-music-comp-co': ['primary_output', 'contribution_certificate'],
        'kra2-c-music-comp-sole': ['primary_output', 'invitation_acceptance', 'performance_proof'],
        'kra2-c-music-perf': ['primary_output', 'invitation_acceptance', 'role_certification'],
        'kra2-c-music-prod-co': ['primary_output', 'contribution_certificate'],
        'kra2-c-music-prod-sole': ['primary_output', 'copyright_registration', 'published_release', 'role_certification'],
        'kra2-c-novel-co': ['primary_output', 'contribution_certificate'],
        'kra2-c-novel-sole': ['primary_output', 'editorial_review', 'publisher_credibility'],
        'kra2-c-playwright-co': ['primary_output', 'contribution_certificate'],
        'kra2-c-playwright-sole': ['primary_output', 'copyright_registration', 'invitation_acceptance', 'production_proof', 'role_certification'],
        'kra2-c-poetry': ['primary_output', 'editorial_review', 'publisher_credibility'],
        'kra2-c-prod-design': ['primary_output', 'design_portfolio', 'media_documentation', 'program_documentation', 'role_certification'],
        'kra2-c-story-co': ['primary_output', 'contribution_certificate'],
        'kra2-c-story-sole': ['primary_output', 'editorial_review', 'publisher_credibility'],
        'kra2-c-visual': ['primary_output', 'invitation_acceptance', 'exhibition_catalog', 'gallery_documentation', 'role_certification'],
      };
      return List<String>.from(criterionCSlots[id] ?? ['primary_output']);
    }
    final slots = <String>['primary_output'];
    if (requiresContributionCertificate(id)) {
      slots.add('contribution_certificate');
    }
    return slots;
  }

  static String slotLabelForIndicator(String slotId, String indicatorId) {
    final id = indicatorId.trim();
    if (id.startsWith('$criterionA-')) {
      switch (slotId) {
        case 'primary_output':
          if (id.contains('book') || id.contains('monograph')) {
            return 'Published book (PDF)';
          }
          if (id.contains('chapter')) return 'Published chapter (PDF)';
          if (id.contains('journal')) return 'Published article (PDF)';
          if (id.contains('translation')) return 'Research output (PDF)';
          if (id.contains('cite')) return 'Your cited article (PDF)';
          return 'Primary evidence (PDF)';
        case 'peer_review_evidence':
          return 'Peer review and academic press evidence';
        case 'indexing_certification':
          return 'Indexing certification (Research Director)';
        case 'contribution_certificate':
          if (id.contains('translation')) {
            return 'Certificate of Contribution (Annex E)';
          }
          return 'Certificate of Contribution (Annex D)';
        case 'citing_publication_evidence':
          return 'Citing article (PDF)';
        case 'translation_impact_evidence':
          return 'Proof of project, policy, or product use';
      }
    }
    if (id.startsWith('$criterionB-')) {
      switch (slotId) {
        case 'primary_output':
          if (id.contains('patent')) return 'IPOPHL patent stage document';
          if (id.contains('comm-')) return 'Commercialization evidence (PDF)';
          if (id.contains('sw-')) return 'Copyright certificate (IPOPHL)';
          if (id.contains('um-') || id.contains('id-')) return 'Registration certificate';
          if (id.contains('variety')) return 'Registration or deposit evidence';
          return 'Primary evidence (PDF)';
        case 'invention_photo':
          return 'Photo of the invention or design';
        case 'president_special_order':
          return 'Special Order signed by the President';
        case 'product_photo':
          return 'Photo of the patented product';
        case 'patent_certificate':
          return 'Invention Patent Certificate';
        case 'licensing_or_cpr_evidence':
          return 'CPR or licensing agreement';
        case 'commercialization_proof':
          return 'Proof of commercialization';
        case 'rd_itso_certification':
          return 'Research Director / ITSO certification';
        case 'project_summary':
          return 'Project summary';
        case 'software_documentation':
          return 'User manual or design documentation';
        case 'utilization_certification':
          return 'End-user utilization certification';
        case 'software_update_description':
          return 'Description of substantial new functionalities';
        case 'registration_deposit_evidence':
          return 'Registration or deposit evidence';
        case 'contribution_certificate':
          if (id.contains('sw-')) return 'Certificate of Contribution (Annex G)';
          if (id.contains('variety')) return 'Certificate of Contribution (Annex H)';
          return 'Certificate of Contribution (Annex F)';
      }
    }
    if (id.startsWith('$criterionC-')) {
      switch (slotId) {
        case 'contribution_certificate':
          return 'Certificate of Contribution (Annex I)';
        case 'invitation_acceptance':
          return 'Proof of invitation or acceptance';
        case 'performance_proof':
          return 'Proof of performance or first performance';
        case 'role_certification':
          return 'Certification of role';
        case 'copyright_registration':
          return 'Copyright registration';
        case 'published_release':
          return 'Published release details';
        case 'production_proof':
          return 'Proof of production or staging';
        case 'program_documentation':
          return 'Program, playbill, or event flyer';
        case 'media_documentation':
          return 'Photo or video documentation';
        case 'design_portfolio':
          return 'Design portfolio or proposal';
        case 'exhibition_catalog':
          return 'Exhibition catalog or brochure';
        case 'gallery_documentation':
          return 'Gallery or venue information';
        case 'exhibition_documentation':
          return 'Exhibition or competition documentation';
        case 'authorship_documentation':
          return 'Authorship documentation';
        case 'organizing_body_info':
          return 'Organizing body or gallery profile';
        case 'festival_program':
          return 'Festival program or screening announcement';
        case 'editorial_review':
          return 'Editorial review evidence';
        case 'publisher_credibility':
          return 'Proof of publisher credibility';
        case 'primary_output':
          return 'Primary creative or performance evidence (PDF)';
      }
    }
    return slotLabel(slotId);
  }

  static String slotLabel(String slotId) {
    switch (slotId) {
      case 'primary_output':
        return 'Your PDF';
      case 'contribution_certificate':
        return 'Shared authorship certificate';
      case 'peer_review_evidence':
        return 'Peer review evidence';
      case 'indexing_certification':
        return 'Indexing certification';
      case 'citing_publication_evidence':
        return 'Citing publication';
      case 'translation_impact_evidence':
        return 'Translation impact evidence';
      default:
        return slotId.replaceAll('_', ' ');
    }
  }

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
