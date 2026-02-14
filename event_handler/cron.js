const cron = require('node-cron');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const { executeAction } = require('./actions');
const log = require('./utils/logger');
const CRON_DIR = path.join(__dirname, 'cron');

/**
 * Load and schedule crons from CRONS.json
 * @returns {Array} - Array of scheduled cron tasks
 */
function loadCrons() {
  const cronFile = path.join(__dirname, '..', 'operating_system', 'CRONS.json');

  log.info('Loading cron jobs');

  if (!fs.existsSync(cronFile)) {
    log.info('No CRONS.json found');
    return [];
  }

  const crons = JSON.parse(fs.readFileSync(cronFile, 'utf8'));
  const tasks = [];

  for (const cronEntry of crons) {
    const { name, schedule, type = 'agent', enabled } = cronEntry;
    if (enabled === false) continue;

    if (!cron.validate(schedule)) {
      log.error({ name, schedule }, 'Invalid cron schedule');
      continue;
    }

    const task = cron.schedule(schedule, async () => {
      try {
        const result = await executeAction(cronEntry, { cwd: CRON_DIR });
        log.info({ name, result: result || 'ran' }, 'Cron job completed');
      } catch (err) {
        log.error({ name, err: err.message }, 'Cron job failed');
      }
    });

    tasks.push({ name, schedule, type, task });
  }

  if (tasks.length === 0) {
    log.info('No active cron jobs');
  } else {
    for (const { name, schedule, type } of tasks) {
      log.info({ name, schedule, type }, 'Cron job registered');
    }
  }

  log.info({ count: tasks.length }, 'Cron jobs loaded');

  return tasks;
}

// Run if executed directly
if (require.main === module) {
  log.info('Starting cron scheduler...');
  loadCrons();
}

module.exports = { loadCrons };
