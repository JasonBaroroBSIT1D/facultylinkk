import 'package:flutter/material.dart';

import '../../data/api_client.dart';
import '../../data/kra2_a_catalog.dart';
import '../../data/kra2_a_ux.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import 'kra2_a_journal_wizard_screen.dart';
import 'kra2_a_review_submit_screen.dart';

/// Journal article home — friendly status list + start 3-step wizard.
class Kra2AJournalHubScreen extends StatefulWidget {
  const Kra2AJournalHubScreen({super.key});

  @override
  State<Kra2AJournalHubScreen> createState() => _Kra2AJournalHubScreenState();
}

class _Kra2AJournalHubScreenState extends State<Kra2AJournalHubScreen> {
  final _api = ApiClient();
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _summary;
  List<Map<String, dynamic>> _rows = const [];

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final summary = await _api.fetchKra2ASummary();
      final acc = await _api.fetchKra2AAccomplishments();
      final rows = acc['accomplishments'];
      if (!mounted) return;
      setState(() {
        _summary = summary;
        _rows = rows is List
            ? rows.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
            : const [];
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Could not refresh. Pull down to try again.';
        _loading = false;
      });
    }
  }

  void _startNew() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const Kra2AJournalWizardScreen()),
    ).then((_) => _refresh());
  }

  void _openRow(Map<String, dynamic> row) {
    final docId = (row['documentId'] ?? '').toString();
    if (docId.isEmpty) return;
    final submitted = (row['submittedForReviewAt'] ?? '').toString().isNotEmpty;
    final status = Kra2AUx.facultyStatus(
      reviewStatus: row['reviewStatus']?.toString(),
      validationStatus: row['validationStatus']?.toString(),
      submittedForReview: submitted,
    );
    final Widget screen = status == Kra2FacultyStatus.draft || status == Kra2FacultyStatus.needsChanges
        ? Kra2AReviewSubmitScreen(primaryDocumentId: docId, onFinished: () => Navigator.pop(context))
        : Kra2AReviewSubmitScreen(primaryDocumentId: docId, onFinished: () => Navigator.pop(context));
    Navigator.push(context, MaterialPageRoute(builder: (_) => screen)).then((_) => _refresh());
  }

  @override
  Widget build(BuildContext context) {
    final verified = (_summary?['validatedPoints'] as num?)?.toDouble() ?? 0;
    final max = (_summary?['maxPoints'] as num?)?.toDouble() ?? 100;
    final draftEst = (_summary?['draftEstimatedSum'] as num?)?.toDouble();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Journal articles'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(_error!, style: const TextStyle(color: Colors.red)),
                    ),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Your Criterion A progress', style: Theme.of(context).textTheme.titleMedium),
                          const SizedBox(height: 8),
                          Text(
                            '${verified.toStringAsFixed(0)} verified of ${max.toStringAsFixed(0)} points possible',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          if (draftEst != null && draftEst > verified)
                            Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(
                                'About ${draftEst.toStringAsFixed(0)} points waiting on review (estimate)',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  PrimaryButton(
                    label: 'Add journal article',
                    icon: Icons.add,
                    onPressed: _startNew,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Three quick steps: choose your article type, upload your PDF, review and submit.',
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  const SizedBox(height: 20),
                  Text('Your submissions', style: Theme.of(context).textTheme.titleMedium),
                  if (_rows.isEmpty)
                    const Padding(
                      padding: EdgeInsets.only(top: 12),
                      child: Text('Nothing here yet. Tap Add journal article to begin.'),
                    )
                  else
                    ..._rows.map((row) {
                      final title = (row['outputTitle'] ?? row['title'] ?? 'Journal article').toString();
                      final submitted = (row['submittedForReviewAt'] ?? '').toString().isNotEmpty;
                      final status = Kra2AUx.facultyStatus(
                        reviewStatus: row['reviewStatus']?.toString(),
                        validationStatus: row['validationStatus']?.toString(),
                        submittedForReview: submitted,
                      );
                      final type = Kra2AJournalCatalog.typeForIndicator(row['indicatorId']?.toString());
                      final ptsLine = Kra2AUx.pointsLine(
                        status: status,
                        estimatedPoints: (row['estimatedPoints'] as num?)?.toDouble(),
                        reviewerAssessedPoints: (row['reviewerAssessedPoints'] as num?)?.toDouble(),
                      );
                      return Card(
                        margin: const EdgeInsets.only(top: 10),
                        child: ListTile(
                          title: Text(title),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(Kra2AUx.statusLabel(status)),
                              if (type != null) Text(type.title, style: Theme.of(context).textTheme.bodySmall),
                              if (ptsLine.isNotEmpty) Text(ptsLine),
                              Text(
                                Kra2AUx.statusExplanation(status),
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                          isThreeLine: true,
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => _openRow(row),
                        ),
                      );
                    }),
                ],
              ),
            ),
    );
  }
}
