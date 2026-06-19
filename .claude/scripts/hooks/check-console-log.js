#!/usr/bin/env node
/**
 * Stop hook: checks for console.log/print() in modified files
 */

const fs = require('fs');
const path = require('path');

try {
  const { isGitRepo, getGitModifiedFiles, log } = require('../lib/utils');

  if (!isGitRepo()) process.exit(0);

  // Check JS/TS files for console.log
  const jsFiles = getGitModifiedFiles(['\\.tsx?$', '\\.jsx?$']);
  const pyFiles = getGitModifiedFiles(['\\.py$']);

  let warnings = [];

  jsFiles.forEach(file => {
    if (!fs.existsSync(file)) return;
    const content = fs.readFileSync(file, 'utf8');
    const lines = content.split('\n');
    lines.forEach((line, idx) => {
      if (/console\.log/.test(line) && !/\/\/.*console\.log/.test(line)) {
        warnings.push(`${file}:${idx + 1}: ${line.trim()}`);
      }
    });
  });

  pyFiles.forEach(file => {
    if (!fs.existsSync(file)) return;
    const content = fs.readFileSync(file, 'utf8');
    const lines = content.split('\n');
    lines.forEach((line, idx) => {
      if (/\bprint\s*\(/.test(line) && !/#.*print/.test(line) && !/logger\./.test(line)) {
        warnings.push(`${file}:${idx + 1}: ${line.trim()}`);
      }
    });
  });

  if (warnings.length > 0) {
    log('[Hook] WARNING: Debug statements found in modified files:');
    warnings.slice(0, 10).forEach(w => log(`  ${w}`));
    log('[Hook] Remove before committing');
  }
} catch (err) {
  // Silent on error
}
