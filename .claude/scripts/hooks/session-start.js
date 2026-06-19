#!/usr/bin/env node
/**
 * SessionStart hook: loads previous context and detects environment
 */

const path = require('path');
const { getSessionsDir, getLearnedSkillsDir, ensureDir, findFiles, log } = require('../lib/utils');

try {
  const sessionsDir = ensureDir(getSessionsDir());
  const learnedDir = ensureDir(getLearnedSkillsDir());

  // Check for recent sessions (last 7 days)
  const recentSessions = findFiles(sessionsDir, '*-session.tmp', { maxAge: 7 });

  if (recentSessions.length > 0) {
    log(`[Session] Found ${recentSessions.length} recent session(s):`);
    recentSessions.slice(0, 3).forEach(s => {
      log(`  - ${path.basename(s.path)}`);
    });
  }

  // Check for learned skills
  const skills = findFiles(learnedDir, '*.md');
  if (skills.length > 0) {
    log(`[Session] ${skills.length} learned skill(s) available`);
  }

  log('[Session] Ready');
} catch (err) {
  // Don't block session start
  log(`[Session] Init warning: ${err.message}`);
}
