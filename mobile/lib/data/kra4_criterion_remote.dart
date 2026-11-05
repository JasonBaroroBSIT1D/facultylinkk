import 'api_client.dart';

/// Cached KRA IV criterion summary + accomplishments from the backend.
class Kra4CriterionSnapshot {
  const Kra4CriterionSnapshot({
    required this.summary,
    required this.accomplishments,
    required this.fetchedAt,
  });

  final Map<String, dynamic> summary;
  final List<Map<String, dynamic>> accomplishments;
  final DateTime fetchedAt;
}

/// In-memory fetch deduplication for KRA IV criterion APIs (cleared on logout).
abstract final class Kra4CriterionRemote {
  static final Map<String, Kra4CriterionSnapshot> _cache = {};
  static final Map<String, Future<Kra4CriterionSnapshot>> _inFlight = {};

  static void invalidate([String? criterionId]) {
    if (criterionId == null || criterionId.isEmpty) {
      _cache.clear();
      _inFlight.clear();
      return;
    }
    _cache.remove(criterionId);
    _inFlight.remove(criterionId);
  }

  static Kra4CriterionSnapshot? cached(String criterionId) => _cache[criterionId];

  static Future<Kra4CriterionSnapshot> fetch(
    String criterionId, {
    ApiClient? api,
    bool forceRefresh = false,
  }) async {
    final cid = criterionId.trim();
    if (!forceRefresh) {
      final hit = _cache[cid];
      if (hit != null) return hit;
      final pending = _inFlight[cid];
      if (pending != null) return pending;
    }

    final client = api ?? ApiClient();
    final future = _load(client, cid);
    _inFlight[cid] = future;
    try {
      final snap = await future;
      _cache[cid] = snap;
      return snap;
    } finally {
      _inFlight.remove(cid);
    }
  }

  static Future<Kra4CriterionSnapshot> _load(ApiClient api, String criterionId) async {
    final results = await Future.wait([
      api.fetchKra4Summary(criterionId),
      api.fetchKra4Accomplishments(criterionId),
    ]);
    final summary = Map<String, dynamic>.from(results[0]);
    final acc = Map<String, dynamic>.from(results[1]);
    final rows = acc['accomplishments'];
    final accomplishments = rows is List
        ? rows.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
        : <Map<String, dynamic>>[];
    return Kra4CriterionSnapshot(
      summary: summary,
      accomplishments: accomplishments,
      fetchedAt: DateTime.now(),
    );
  }
}
