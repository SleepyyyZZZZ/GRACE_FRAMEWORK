#!/usr/bin/env node
/**
 * Suggest context compaction at strategic intervals
 * Tracks tool call count per session, suggests compaction after threshold
 */

const path = require('path');
const fs = require('fs');
const os = require('os');

try {
  const threshold = parseInt(process.env.COMPACT_THRESHOLD || '50', 10);
  const sessionId = process.env.CLAUDE_SESSION_ID || process.pid.toString();
  const counterFile = path.join(os.tmpdir(), `claude-compact-${sessionId.slice(-8)}.count`);

  // Read current count
  let count = 0;
  if (fs.existsSync(counterFile)) {
    count = parseInt(fs.readFileSync(counterFile, 'utf8').trim() || '0', 10);
  }

  // Increment
  count++;
  fs.writeFileSync(counterFile, count.toString(), 'utf8');

  // Check thresholds
  if (count === threshold) {
    console.error(`[Compact] ${threshold} tool calls reached. Consider running /compact`);
    console.error('[Compact] Good times: after finishing a plan, after resolving a bug, before switching tasks');
  } else if (count > threshold && (count - threshold) % 25 === 0) {
    console.error(`[Compact] ${count} tool calls. Reminder: /compact to free context`);
  }

  // Pass through stdin to stdout
  let data = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { data += chunk; });
  process.stdin.on('end', () => { console.log(data); });
} catch (err) {
  // Never block on error
  let data = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { data += chunk; });
  process.stdin.on('end', () => { console.log(data); });
}
