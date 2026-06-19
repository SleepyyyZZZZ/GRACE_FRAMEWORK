/**
 * Cross-platform utility functions for Claude Code hooks and scripts
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawnSync } = require('child_process');

const isWindows = process.platform === 'win32';
const isMacOS = process.platform === 'darwin';
const isLinux = process.platform === 'linux';

function getHomeDir() { return os.homedir(); }
function getClaudeDir() { return path.join(getHomeDir(), '.claude'); }
function getSessionsDir() { return path.join(getClaudeDir(), 'sessions'); }
function getLearnedSkillsDir() { return path.join(getClaudeDir(), 'skills', 'learned'); }
function getTempDir() { return os.tmpdir(); }

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  return dirPath;
}

function getDateString() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

function getTimeString() {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
}

function getDateTimeString() {
  const now = new Date();
  return `${getDateString()} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
}

function getGitRepoName() {
  const result = runCommand('git rev-parse --show-toplevel');
  if (!result.success) return null;
  return path.basename(result.output);
}

function getProjectName() {
  return getGitRepoName() || path.basename(process.cwd()) || null;
}

function getSessionIdShort(fallback = 'default') {
  const sessionId = process.env.CLAUDE_SESSION_ID;
  if (sessionId && sessionId.length > 0) return sessionId.slice(-8);
  return getProjectName() || fallback;
}

function findFiles(dir, pattern, options = {}) {
  const { maxAge = null, recursive = false } = options;
  const results = [];
  if (!fs.existsSync(dir)) return results;

  const regexPattern = pattern.replace(/\./g, '\\.').replace(/\*/g, '.*').replace(/\?/g, '.');
  const regex = new RegExp(`^${regexPattern}$`);

  function searchDir(currentDir) {
    try {
      const entries = fs.readdirSync(currentDir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(currentDir, entry.name);
        if (entry.isFile() && regex.test(entry.name)) {
          const stats = fs.statSync(fullPath);
          if (maxAge !== null) {
            const ageInDays = (Date.now() - stats.mtimeMs) / (1000 * 60 * 60 * 24);
            if (ageInDays <= maxAge) results.push({ path: fullPath, mtime: stats.mtimeMs });
          } else {
            results.push({ path: fullPath, mtime: stats.mtimeMs });
          }
        } else if (entry.isDirectory() && recursive) {
          searchDir(fullPath);
        }
      }
    } catch (_err) { /* ignore permission errors */ }
  }

  searchDir(dir);
  results.sort((a, b) => b.mtime - a.mtime);
  return results;
}

async function readStdinJson() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { data += chunk; });
    process.stdin.on('end', () => {
      try { resolve(data.trim() ? JSON.parse(data) : {}); }
      catch (err) { reject(err); }
    });
    process.stdin.on('error', reject);
  });
}

function log(message) { console.error(message); }
function output(data) { console.log(typeof data === 'object' ? JSON.stringify(data) : data); }

function readFile(filePath) {
  try { return fs.readFileSync(filePath, 'utf8'); }
  catch { return null; }
}

function writeFile(filePath, content) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content, 'utf8');
}

function appendFile(filePath, content) {
  ensureDir(path.dirname(filePath));
  fs.appendFileSync(filePath, content, 'utf8');
}

function runCommand(cmd, options = {}) {
  try {
    const result = execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'], ...options });
    return { success: true, output: result.trim() };
  } catch (err) {
    return { success: false, output: err.stderr || err.message };
  }
}

function isGitRepo() { return runCommand('git rev-parse --git-dir').success; }

function getGitModifiedFiles(patterns = []) {
  if (!isGitRepo()) return [];
  const result = runCommand('git diff --name-only HEAD');
  if (!result.success) return [];
  let files = result.output.split('\n').filter(Boolean);
  if (patterns.length > 0) {
    files = files.filter(file => patterns.some(p => new RegExp(p).test(file)));
  }
  return files;
}

module.exports = {
  isWindows, isMacOS, isLinux,
  getHomeDir, getClaudeDir, getSessionsDir, getLearnedSkillsDir, getTempDir, ensureDir,
  getDateString, getTimeString, getDateTimeString,
  getSessionIdShort, getGitRepoName, getProjectName,
  findFiles, readFile, writeFile, appendFile,
  readStdinJson, log, output,
  runCommand, isGitRepo, getGitModifiedFiles
};
