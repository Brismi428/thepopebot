import { execSync, exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);
/**
 * Check if a command exists
 */
function commandExists(cmd) {
  try {
    execSync(`where ${cmd}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}
/**
 * Get Node.js version
 */
function getNodeVersion() {
  try {
    const version = execSync('node --version', { encoding: 'utf-8' }).trim();
    return version.replace('v', '');
  } catch {
    return null;
  }
}
/**
 * Check if gh CLI is authenticated
 */
async function isGhAuthenticated() {
  try {
    await execAsync('gh auth status');
    return true;
  } catch {
    return false;
  }
}
/**
 * Get git remote info (owner/repo)
 */
function getGitRemoteInfo() {
  try {
    const remote = execSync('git remote get-url origin', { encoding: 'utf-8' }).trim();
    const httpsMatch = remote.match(/github\.com\/([^/]+)\/([^/.]+)/);
    const sshMatch = remote.match(/github\.com:([^/]+)\/([^/.]+)/);
    const match = httpsMatch || sshMatch;
    if (match) {
      return { owner: match[1], repo: match[2].replace('.git', '') };
    }
    return null;
  } catch {
    return null;
  }
}
/**
 * Get package manager (pnpm preferred, npm fallback)
 */
function getPackageManager() {
  if (commandExists('pnpm')) return 'pnpm';
  if (commandExists('npm')) return 'npm';
  return null;
}
/**
 * Check all prerequisites and return status
 */
export async function checkPrerequisites() {
  const results = {
    node: { installed: false, version: null, ok: false },
    packageManager: { installed: false, name: null },
    gh: { installed: false, authenticated: false },
    ngrok: { installed: false },
    git: { installed: false, remoteInfo: null },
  };
  const nodeVersion = getNodeVersion();
  if (nodeVersion) {
    results.node.installed = true;
    results.node.version = nodeVersion;
    const [major] = nodeVersion.split('.').map(Number);
    results.node.ok = major >= 18;
  }
  const pm = getPackageManager();
  if (pm) {
    results.packageManager.installed = true;
    results.packageManager.name = pm;
  }
  results.gh.installed = commandExists('gh');
  if (results.gh.installed) {
    results.gh.authenticated = await isGhAuthenticated();
  }
  results.ngrok.installed = commandExists('ngrok');
  results.git.installed = commandExists('git');
  if (results.git.installed) {
    results.git.remoteInfo = getGitRemoteInfo();
  }
  return results;
}
/**
 * Install a global npm package
 */
export async function installGlobalPackage(packageName) {
  const pm = getPackageManager();
  const cmd = pm === 'pnpm' ? `pnpm add -g ${packageName}` : `npm install -g ${packageName}`;
  await execAsync(cmd);
}
/**
 * Run gh auth login
 */
export async function runGhAuth() {
  execSync('gh auth login', { stdio: 'inherit' });
}
export { commandExists, getGitRemoteInfo, getPackageManager };

