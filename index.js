const fs = require('fs');
const { execSync } = require('child_process');

function run(cmd) {
  try { execSync(cmd, { stdio: 'inherit' }); }
  catch (e) { console.error('Error:', e.message); }
}

const REPO = 'https://github.com/somethingosmething-hue/devop';

// Preserve config and .env before updating
let savedEnv = '';
let savedConfig = '';
if (fs.existsSync('.env')) {
  savedEnv = fs.readFileSync('.env', 'utf8');
  console.log(' Saved existing .env');
}
if (fs.existsSync('config.toml')) {
  savedConfig = fs.readFileSync('config.toml', 'utf8');
  console.log(' Saved existing config.toml');
}

if (!fs.existsSync('./main.py') || !fs.existsSync('./language')) {
  console.log(' Cloning repo...');
  run('rm -rf _tmp_clone');
  run(`git clone --depth 1 ${REPO} _tmp_clone`);
  run('cp -r _tmp_clone/* .');
  run('find _tmp_clone -maxdepth 1 -name ".*" ! -name "." -exec cp -r {} . \\;');
  run('rm -rf _tmp_clone');
  console.log(' Installing dependencies...');
  run('pip install -e .');
} else {
  let isGitRepo = false;
  try {
    execSync('git rev-parse --git-dir', { stdio: 'pipe' });
    isGitRepo = true;
  } catch {}
  if (isGitRepo) {
    console.log(' Updating from GitHub...');
    try { run('git fetch origin main'); } catch {}
    try { run('git stash'); } catch {}
    try { run('git reset --hard origin/main'); } catch {}
    console.log(' Installing dependency updates...');
    try { run('pip install -e .'); } catch {}
  } else {
    console.log(' Not a git repo, skipping update...');
  }
}

// Restore config
if (savedEnv && !fs.existsSync('.env')) {
  fs.writeFileSync('.env', savedEnv);
  console.log(' Restored .env');
}
if (savedConfig) {
  fs.writeFileSync('config.toml', savedConfig);
  console.log(' Restored config.toml');
}

console.log(' Starting bot...');
run('python main.py');
