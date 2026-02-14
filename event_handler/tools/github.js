const { TtlCache } = require('../utils/cache');

const { GH_TOKEN, GH_OWNER, GH_REPO } = process.env;

// Cache for GitHub API responses (workflow runs: 30s, job details: 30s)
const ghCache = new TtlCache(30000);

/**
 * GitHub REST API helper with authentication
 * @param {string} endpoint - API endpoint (e.g., '/repos/owner/repo/...')
 * @param {object} options - Fetch options (method, body, headers)
 * @returns {Promise<object>} - Parsed JSON response
 */
async function githubApi(endpoint, options = {}) {
  const res = await fetch(`https://api.github.com${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${GH_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`GitHub API error: ${res.status} ${error}`);
  }

  return res.json();
}

/**
 * Get workflow runs with optional status filter (cached for 30s)
 * @param {string} [status] - Filter by status (in_progress, queued, completed)
 * @returns {Promise<object>} - Workflow runs response
 */
async function getWorkflowRuns(status) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  params.set('per_page', '20');

  const query = params.toString();
  const cacheKey = `runs:${query}`;
  return ghCache.getOrSet(cacheKey, () =>
    githubApi(`/repos/${GH_OWNER}/${GH_REPO}/actions/runs?${query}`)
  , 30000);
}

/**
 * Get jobs for a specific workflow run (cached for 30s)
 * @param {number} runId - Workflow run ID
 * @returns {Promise<object>} - Jobs response with steps
 */
async function getWorkflowRunJobs(runId) {
  const cacheKey = `run-jobs:${runId}`;
  return ghCache.getOrSet(cacheKey, () =>
    githubApi(`/repos/${GH_OWNER}/${GH_REPO}/actions/runs/${runId}/jobs`)
  , 30000);
}

/**
 * Get job status for running/recent jobs
 * @param {string} [jobId] - Optional specific job ID to filter by
 * @returns {Promise<object>} - Status summary with jobs array
 */
async function getJobStatus(jobId) {
  // Fetch both in_progress and queued runs
  const [inProgress, queued] = await Promise.all([
    getWorkflowRuns('in_progress'),
    getWorkflowRuns('queued'),
  ]);

  const allRuns = [...(inProgress.workflow_runs || []), ...(queued.workflow_runs || [])];

  // Filter to only job/* branches
  const jobRuns = allRuns.filter(run => run.head_branch?.startsWith('job/'));

  // If specific job requested, filter further
  const filteredRuns = jobId
    ? jobRuns.filter(run => run.head_branch === `job/${jobId}`)
    : jobRuns;

  // Get detailed job info for each run
  const jobs = await Promise.all(
    filteredRuns.map(async (run) => {
      const extractedJobId = run.head_branch.slice(4); // Remove 'job/' prefix
      const startedAt = new Date(run.created_at);
      const durationMinutes = Math.round((Date.now() - startedAt.getTime()) / 60000);

      let currentStep = null;
      let stepsCompleted = 0;
      let stepsTotal = 0;

      try {
        const jobsData = await getWorkflowRunJobs(run.id);
        if (jobsData.jobs?.length > 0) {
          const job = jobsData.jobs[0];
          stepsTotal = job.steps?.length || 0;
          stepsCompleted = job.steps?.filter(s => s.status === 'completed').length || 0;
          currentStep = job.steps?.find(s => s.status === 'in_progress')?.name || null;
        }
      } catch (err) {
        // Jobs endpoint may fail if run hasn't started yet
      }

      return {
        job_id: extractedJobId,
        branch: run.head_branch,
        status: run.status,
        started_at: run.created_at,
        duration_minutes: durationMinutes,
        current_step: currentStep,
        steps_completed: stepsCompleted,
        steps_total: stepsTotal,
        run_id: run.id,
      };
    })
  );

  // Count only job/* branches, not all workflows
  const runningCount = jobs.filter(j => j.status === 'in_progress').length;
  const queuedCount = jobs.filter(j => j.status === 'queued').length;

  return {
    jobs,
    queued: queuedCount,
    running: runningCount,
  };
}

/**
 * Get a catalog of all systems in the repo (cached for 120s).
 * Lists each system directory with file count, key files, and last commit date.
 * @returns {Promise<Array>} - Array of system info objects
 */
async function getSystemsCatalog() {
  return ghCache.getOrSet('systems-catalog', async () => {
    const contents = await githubApi(`/repos/${GH_OWNER}/${GH_REPO}/contents/systems`);

    if (!Array.isArray(contents)) return [];

    const systems = await Promise.all(
      contents
        .filter(item => item.type === 'dir')
        .map(async (dir) => {
          let fileCount = 0;
          let hasClaude = false;
          let hasWorkflow = false;

          try {
            const files = await githubApi(`/repos/${GH_OWNER}/${GH_REPO}/contents/systems/${dir.name}`);
            if (Array.isArray(files)) {
              fileCount = files.length;
              hasClaude = files.some(f => f.name === 'CLAUDE.md');
              hasWorkflow = files.some(f => f.name === 'workflow.md');
            }
          } catch {
            // directory listing failed — keep defaults
          }

          let lastCommitDate = null;
          try {
            const commits = await githubApi(
              `/repos/${GH_OWNER}/${GH_REPO}/commits?path=systems/${dir.name}&per_page=1`
            );
            if (commits.length > 0) {
              lastCommitDate = commits[0].commit.committer.date;
            }
          } catch {
            // commit lookup failed — keep null
          }

          return {
            name: dir.name,
            file_count: fileCount,
            has_claude_md: hasClaude,
            has_workflow_md: hasWorkflow,
            last_commit: lastCommitDate,
          };
        })
    );

    return systems;
  }, 120000);
}

/**
 * Get available PRP templates with parsed frontmatter (cached for 300s).
 * Fetches from PRPs/templates/, excludes prp_base.md.
 * @returns {Promise<Array>} - Array of template objects with name, keywords, description, filename
 */
async function getTemplates() {
  return ghCache.getOrSet('prp-templates', async () => {
    const contents = await githubApi(`/repos/${GH_OWNER}/${GH_REPO}/contents/PRPs/templates`);

    if (!Array.isArray(contents)) return [];

    const templateFiles = contents.filter(
      f => f.name.endsWith('.md') && f.name !== 'prp_base.md'
    );

    const templates = await Promise.all(
      templateFiles.map(async (file) => {
        try {
          const data = await githubApi(`/repos/${GH_OWNER}/${GH_REPO}/contents/PRPs/templates/${file.name}`);
          const content = Buffer.from(data.content, 'base64').toString('utf8');

          // Extract YAML frontmatter between --- delimiters
          const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
          if (!fmMatch) {
            return { filename: file.name, name: file.name.replace('.md', ''), keywords: '', description: '' };
          }

          const fm = fmMatch[1];
          const nameMatch = fm.match(/^name:\s*(.+)$/m);
          const keywordsMatch = fm.match(/^keywords:\s*(.+)$/m);
          const descMatch = fm.match(/^description:\s*(.+)$/m);

          return {
            filename: file.name,
            name: nameMatch ? nameMatch[1].trim() : file.name.replace('.md', ''),
            keywords: keywordsMatch ? keywordsMatch[1].trim() : '',
            description: descMatch ? descMatch[1].trim() : '',
          };
        } catch {
          return { filename: file.name, name: file.name.replace('.md', ''), keywords: '', description: '' };
        }
      })
    );

    return templates;
  }, 300000);
}

module.exports = { githubApi, getWorkflowRuns, getWorkflowRunJobs, getJobStatus, getSystemsCatalog, getTemplates };
