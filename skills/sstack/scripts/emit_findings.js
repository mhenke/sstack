#!/usr/bin/env node
/**
 * Evidence emitter: the only writer of .sstack/findings/* and .sstack/report.json.
 * Node.js stdlib-only equivalent to emit_findings.py. Recorded paths are
 * rewritten host-repo-relative at capture, so evidence diffs clean
 * across machines and checkouts.
 *
 * Two invocation modes: a finding JSON on stdin or --finding <file>
 * emits that one finding immediately; empty stdin runs the upgrade
 * pass — every findings/<slug>.json whose repro is a command string
 * is executed and fingerprinted now (requests become evidence only
 * through execution).
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

const VERDICTS = new Set(['confirmed', 'refuted', 'inconclusive']);
const STATES = new Set(['red', 'green']);
const SAFE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

function safeSlug(value, field) {
  if (!value || !SAFE.test(value) || value === '.' || value === '..') {
    throw new Error(
      `${field} must be a plain filename fragment (letters, digits, dot, dash, underscore): ${JSON.stringify(value)}`
    );
  }
  return value;
}

function readFinding(findingPath, rawStdin) {
  let input;
  if (findingPath) {
    try {
      input = fs.readFileSync(findingPath, 'utf8');
    } catch (err) {
      process.stderr.write(`cannot read --finding file: ${err.message}\n`);
      process.exit(2);
    }
  } else {
    input = rawStdin;
  }
  if (!input.trim()) {
    process.stderr.write(
      `no finding ${findingPath ? `in ${findingPath}` : 'on stdin'} — write the finding JSON to a file and pass --finding <file>, e.g.:
node scripts/emit_findings.js --workspace <host-repo> --finding finding.json
{"slug": "checkout-page-zero", "lens": "boundaries", "surface": "checkout",
 "case": "checkout(items=[], page=0)", "oracle": "ValueError naming page",
 "verdict": "confirmed", "repro": "<command that reproduces it>",
 "regression": {"file": "tests/test_checkout.py", "test": "test_page_zero",
                "before": "red", "after": "green"}}
JSON
`);
    process.exit(2);
  }
  let finding;
  try {
    finding = JSON.parse(input);
  } catch (err) {
    throw new Error(`invalid finding: ${err.message}`);
  }

  if (!finding || typeof finding !== 'object' || Array.isArray(finding)) {
    throw new Error('finding must be a JSON object');
  }

  const missing = ['lens', 'surface', 'case', 'oracle', 'verdict', 'repro'].filter(
    (k) => !finding[k]
  );
  if (missing.length > 0) {
    throw new Error(`missing fields: ${missing.join(', ')}`);
  }

  if (!VERDICTS.has(finding.verdict)) {
    throw new Error(`verdict must be one of ${Array.from(VERDICTS).join(', ')}`);
  }

  const regression = finding.regression;
  if (!regression || typeof regression !== 'object' || Array.isArray(regression)) {
    throw new Error('regression must name file, test, before, after');
  }

  const absent = ['file', 'test', 'before', 'after'].filter((k) => !regression[k]);
  if (absent.length > 0) {
    throw new Error(`regression missing: ${absent.join(', ')}`);
  }

  for (const state of ['before', 'after']) {
    if (!STATES.has(regression[state])) {
      throw new Error(`regression.${state} must be the literal token 'red' or 'green'`);
    }
  }

  return finding;
}

// A scratch probe that does not compile is infrastructure failure, not
// evidence. Compile referenced scratch probes before anything is recorded.
const PROBE_CHECK = {
  '.py': ['python3', '-m', 'py_compile'],
  '.js': ['node', '--check'],
};

function preflightProbe(command, workspace) {
  for (const token of command.split(/\s+/)) {
    const probe = path.isAbsolute(token) ? token : path.join(workspace, token);
    if (!/\.(py|js)$/.test(probe) || !probe.split(path.sep).includes('scratch')) continue;
    const [cmd, ...args] = PROBE_CHECK[probe.endsWith('.py') ? '.py' : '.js'];
    const check = spawnSync(cmd, [...args, probe], { encoding: 'utf8' });
    if (check.status !== 0) {
      process.stderr.write(`scratch probe does not compile — repair it before emitting: ${probe}\n${check.stderr || ''}\n`);
      return false;
    }
  }
  return true;
}

// Evidence is diffed run over run, so the recorded bytes must not carry
// the absolute workspace path: it differs on every machine and every
// temp checkout, and a path that moved reads as a false change. Rewrite
// it to `.` on path boundaries — a sibling directory sharing the
// prefix stays intact.
function normalize(text, workspace) {
  const escaped = String(workspace).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return text.replace(new RegExp(escaped + '(?![\\w.-])', 'g'), '.');
}

function runRepro(command, workspace) {
  const result = spawnSync(command, {
    shell: true,
    cwd: workspace,
    encoding: 'utf8',
  });
  const stdout = normalize(result.stdout || '', workspace);
  const stderr = normalize(result.stderr || '', workspace);
  const exitCode = result.status !== null ? result.status : (result.signal ? 128 : 1);
  const fingerprint = crypto
    .createHash('sha256')
    .update(stdout + stderr)
    .digest('hex')
    .slice(0, 16);

  return {
    command: normalize(command, workspace),
    exit_code: exitCode,
    stdout,
    stderr,
    fingerprint,
  };
}

function renderMarkdown(finding, run) {
  const observed = (run.stdout + run.stderr).replace(/^\n+|\n+$/g, '');
  const parts = [
    `# ${finding.surface} — ${finding.case}`,
    '',
    `lens: ${finding.lens} | verdict: ${finding.verdict}`,
    '',
    '## Case',
    finding.case,
    '',
    '## Oracle',
    finding.oracle,
    '',
    '## Observed',
    '```',
    observed,
    '```',
    '',
    '## Repro',
    '```',
    run.command,
    '```',
    `exit ${run.exit_code}, fingerprint ${run.fingerprint}`,
  ];

  if (finding.seed !== undefined || finding.counterexample !== undefined) {
    const pbtLines = [];
    if (finding.seed !== undefined) {
      pbtLines.push(`seed: \`${finding.seed}\``);
    }
    if (finding.counterexample !== undefined) {
      pbtLines.push(`counterexample: \`${finding.counterexample}\``);
    }
    parts.push('', '## PBT', pbtLines.join('\n'));
  }

  const regression = finding.regression;
  if (finding.verdict === 'confirmed' && finding.fix) {
    parts.push('', '## Fix', finding.fix);
  }
  parts.push(
    '',
    '## Regression',
    `\`${regression.file}::${regression.test}\` — ${regression.before} → ${regression.after}`
  );

  return parts.join('\n') + '\n';
}

function rebuildReport(findingsDir, workspace, fixture) {
  const files = fs
    .readdirSync(findingsDir)
    .filter((f) => f.endsWith('.json'))
    .sort();

  const entries = [];
  for (const file of files) {
    const record = JSON.parse(fs.readFileSync(path.join(findingsDir, file), 'utf8'));
    if (record.fingerprint === undefined) {
      continue; // a request (no executed repro yet) is not evidence
    }
    const entry = {
      seed_id: record.seed_id || 'other',
      lens: record.lens,
      surface: record.surface,
      case: record.case,
      oracle: record.oracle,
      observed: record.stdout + record.stderr,
      verdict: record.verdict,
      repro: record.command,
      regression: record.regression,
    };
    if (record.seed !== undefined) {
      entry.seed = record.seed;
    }
    if (record.counterexample !== undefined) {
      entry.counterexample = record.counterexample;
    }
    entries.push(entry);
  }

  const reportPath = path.join(workspace, '.sstack', 'report.json');
  fs.writeFileSync(
    reportPath,
    JSON.stringify({ fixture, findings: entries }, null, 2) + '\n'
  );
  return entries.length;
}

function warnUnlanded(finding, workspace) {
  const regression = finding.regression;
  const filePath = path.join(workspace, regression.file);
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    process.stderr.write(`warning: ${regression.file} not on disk yet\n`);
  } else {
    const content = fs.readFileSync(filePath, 'utf8');
    if (!content.includes(regression.test)) {
      process.stderr.write(`warning: '${regression.test}' not found in ${regression.file} yet\n`);
    }
  }
}

// Requests become evidence only through execution: a request whose repro
// is a command string is executed here; one without a command stays a
// request — the machine never invents the missing command.
function upgradeRequests(findingsDir, workspace, fixture) {
  let upgraded = 0;
  let pending = 0;
  const files = fs
    .readdirSync(findingsDir)
    .filter((f) => f.endsWith('.json'))
    .sort();

  for (const file of files) {
    const fullPath = path.join(findingsDir, file);
    const finding = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
    if (finding.fingerprint !== undefined) {
      continue; // already evidence
    }
    let repro = finding.repro;
    if (repro !== null && typeof repro === 'object') {
      repro = repro.command; // the evidence-view shape nests the command
    }
    if (typeof repro !== 'string' || !repro.trim() || !preflightProbe(repro, workspace)) {
      pending += 1;
      continue;
    }
    const run = runRepro(repro, workspace);
    const record = { ...finding };
    delete record.repro;
    Object.assign(record, run);
    fs.writeFileSync(fullPath, JSON.stringify(record, null, 2) + '\n');
    fs.writeFileSync(
      path.join(findingsDir, file.replace(/\.json$/, '.md')),
      renderMarkdown(finding, run)
    );
    warnUnlanded(finding, workspace);
    process.stdout.write(
      `upgraded ${file.replace(/\.json$/, '')}: exit ${run.exit_code}, fingerprint ${run.fingerprint}\n`
    );
    upgraded += 1;
  }

  if (upgraded && fixture) {
    const total = rebuildReport(findingsDir, workspace, fixture);
    process.stdout.write(`report.json now ${total} finding(s)\n`);
  }
  process.stdout.write(`${upgraded} request(s) upgraded, ${pending} still pending (no executable repro)\n`);
  return 0;
}

function main() {
  const args = process.argv.slice(2);
  let workspaceArg = null;
  let fixtureArg = null;
  let findingPath = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--workspace') {
      workspaceArg = args[++i];
    } else if (args[i] === '--fixture') {
      fixtureArg = args[++i];
    } else if (args[i] === '--finding') {
      findingPath = args[++i];
    }
  }

  if (!workspaceArg) {
    process.stderr.write('error: --workspace is required\n');
    process.exit(2);
  }

  const workspace = path.resolve(workspaceArg);
  const stack = path.join(workspace, '.sstack');
  const findingsDir = path.join(stack, 'findings');

  fs.mkdirSync(findingsDir, { recursive: true });

  const reportPath = path.join(stack, 'report.json');
  let fixture = fixtureArg;
  if (!fixture && fs.existsSync(reportPath)) {
    try {
      const existing = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
      fixture = existing.fixture;
    } catch (_) {}
  }

  // Empty stdin without --finding is the upgrade pass, not an error.
  let rawInput = null;
  if (findingPath === null) {
    rawInput = fs.readFileSync(0, 'utf8');
    if (!rawInput.trim()) {
      return upgradeRequests(findingsDir, workspace, fixture);
    }
  }

  let finding;
  try {
    finding = readFinding(findingPath, rawInput);
  } catch (err) {
    process.stderr.write(`invalid finding: ${err.message}\n`);
    process.exit(2);
  }

  if (!fixture) {
    process.stderr.write('first emit needs --fixture\n');
    process.exit(2);
  }

  let slug;
  try {
    slug = safeSlug(
      finding.slug ||
        `${safeSlug(finding.lens, 'lens')}-${safeSlug(finding.surface, 'surface')}`,
      'slug'
    );
  } catch (err) {
    process.stderr.write(`invalid finding: ${err.message}\n`);
    process.exit(2);
  }

  if (!preflightProbe(finding.repro, workspace)) process.exit(3);
  const run = runRepro(finding.repro, workspace);
  const record = {
    seed_id: finding.seed_id || 'other',
    lens: finding.lens,
    surface: finding.surface,
    case: finding.case,
    oracle: finding.oracle,
    verdict: finding.verdict,
    ...run,
    regression: finding.regression,
  };
  if (finding.fix) {
    record.fix = finding.fix;
  }
  if (finding.seed !== undefined) {
    record.seed = finding.seed;
  }
  if (finding.counterexample !== undefined) {
    record.counterexample = finding.counterexample;
  }

  fs.writeFileSync(path.join(findingsDir, `${slug}.json`), JSON.stringify(record, null, 2) + '\n');
  fs.writeFileSync(path.join(findingsDir, `${slug}.md`), renderMarkdown(finding, run));
  const total = rebuildReport(findingsDir, workspace, fixture);
  warnUnlanded(finding, workspace);
  process.stdout.write(
    `emitted ${slug}: ${finding.verdict}, exit ${run.exit_code}, fingerprint ${run.fingerprint}; report.json now ${total} finding(s)\n`
  );
  process.exit(0);
}

main();
