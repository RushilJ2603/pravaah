import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';

import '../../../core/api/error_helper.dart';
import '../../../core/api/session.dart';
import '../../../theme/app_theme.dart';
import '../../conductor/presentation/conductor_screen.dart';
import '../../operator/presentation/operator_screen.dart';

/// Staff entry point: sign in, then show whichever console the token allows.
///
/// The role comes from the backend's response, not from a choice made here.
/// A conductor cannot reach the operator console by picking it in the UI --
/// every admin endpoint is gated server-side regardless.
class StaffScreen extends ConsumerWidget {
  const StaffScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    if (session == null) return const _SignInView();
    if (session.isOperator) return const OperatorScreen();
    if (session.isConductor) return const ConductorScreen();
    return Scaffold(
      body: Center(child: Text('Unsupported role: ${session.role}')),
    );
  }
}

class _SignInView extends ConsumerStatefulWidget {
  const _SignInView();

  @override
  ConsumerState<_SignInView> createState() => _SignInViewState();
}

class _SignInViewState extends ConsumerState<_SignInView> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(sessionProvider.notifier)
          .signIn(_username.text.trim(), _password.text);
    } on ApiException catch (e) {
      setState(() => _error = e.friendlyMessage);
    } catch (_) {
      setState(() => _error = 'Could not sign in.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.badge_outlined,
                      size: 48, color: AppTheme.primaryBlue),
                  const SizedBox(height: 16),
                  Text('Staff sign in',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 8),
                  const Text(
                    'Operators and conductors only. Passengers do not sign in.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                  ),
                  const SizedBox(height: 24),
                  TextField(
                    controller: _username,
                    autocorrect: false,
                    enableSuggestions: false,
                    decoration: const InputDecoration(
                      labelText: 'Username',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _password,
                    obscureText: true,
                    onSubmitted: (_) => _submit(),
                    decoration: const InputDecoration(
                      labelText: 'Password',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.lock_outline),
                    ),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(_error!,
                        style: const TextStyle(color: Color(0xFFB71C1C), fontSize: 13)),
                  ],
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: _busy ? null : _submit,
                    child: _busy
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Sign in'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
