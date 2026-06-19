#!/usr/bin/env node
/**
 * PreCompact hook: saves state before context compaction
 */

const path = require('path');
const { getSessionsDir, getDateTimeString, findFiles, appendFile, log } = require('../lib/utils');

try {
  const sessionsDir = getSessionsDir();
  const timestamp = getDateTimeString();

  // Log compaction event
  const logFile = path.join(sessionsDir, 'compaction-log.txt');
  appendFile(logFile, `[${timestamp}] Context compaction triggered\n`);

  // Mark active session files
  const activeSessions = findFiles(sessionsDir, '*-session.tmp', { maxAge: 1 });
  if (activeSessions.length > 0) {
    const sessionFile = activeSessions[0].path;
    appendFile(sessionFile, `\n## Compaction at ${timestamp}\nContext was summarized at this point.\n`);
  }

  log('[Compact] State preserved before compaction');
} catch (err) {
  log(`[Compact] Warning: ${err.message}`);
}
