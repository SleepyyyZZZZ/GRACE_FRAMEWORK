#!/usr/bin/env node
/**
 * SessionEnd hook: persists session state
 */

const path = require('path');
const fs = require('fs');
const { getSessionsDir, getDateString, getTimeString, getSessionIdShort, ensureDir, writeFile, readFile, log } = require('../lib/utils');

try {
  const sessionsDir = ensureDir(getSessionsDir());
  const today = getDateString();
  const time = getTimeString();
  const shortId = getSessionIdShort();
  const sessionFile = path.join(sessionsDir, `${today}-${shortId}-session.tmp`);

  if (fs.existsSync(sessionFile)) {
    // Update existing session
    let content = readFile(sessionFile);
    if (content) {
      content = content.replace(/Last Updated: .*/, `Last Updated: ${today} ${time}`);
      writeFile(sessionFile, content);
    }
  } else {
    // Create new session file
    const template = `# Session: ${today} ${time}
Session ID: ${shortId}
Last Updated: ${today} ${time}

## Current State
[Describe current state]

## Completed
-

## In Progress
-

## Notes for Next Session
-

## Context to Load
-
`;
    writeFile(sessionFile, template);
  }

  log(`[Session] State saved: ${path.basename(sessionFile)}`);
} catch (err) {
  log(`[Session] Save warning: ${err.message}`);
}
