const { createJob } = require('../tools/create-job');
const { getJobStatus, getSystemsCatalog, getTemplates } = require('../tools/github');

const toolDefinitions = [
  {
    name: 'create_job',
    description:
      'Create an autonomous job for thepopebot to execute. Use this tool liberally - if the user asks for ANY task to be done, create a job. Jobs can handle code changes, file updates, research tasks, web scraping, data analysis, or anything requiring autonomous work. When the user explicitly asks for a job, ALWAYS use this tool. Returns the job ID and branch name.',
    input_schema: {
      type: 'object',
      properties: {
        job_description: {
          type: 'string',
          description:
            'Detailed job description including context and requirements. Be specific about what needs to be done.',
        },
      },
      required: ['job_description'],
    },
  },
  {
    name: 'get_job_status',
    description:
      'Check status of running jobs. Returns list of active workflow runs with timing and current step. Use when user asks about job progress, running jobs, or job status.',
    input_schema: {
      type: 'object',
      properties: {
        job_id: {
          type: 'string',
          description:
            'Optional: specific job ID to check. If omitted, returns all running jobs.',
        },
      },
      required: [],
    },
  },
  {
    name: 'list_templates',
    description:
      'List available PRP templates for building new systems. Templates provide pre-structured blueprints for common system types. Optionally filter by a query string that matches template names, keywords, or descriptions.',
    input_schema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description:
            'Optional search query to filter templates by name, keywords, or description.',
        },
      },
      required: [],
    },
  },
  {
    name: 'run_system',
    description:
      'Run an existing system from the systems catalog. Validates that the system exists, then creates an autonomous job that reads the system\'s CLAUDE.md and workflow.md and executes it with the given input. Use when the user wants to trigger or compose an existing system.',
    input_schema: {
      type: 'object',
      properties: {
        system_name: {
          type: 'string',
          description:
            'Name of the system to run (must exist in systems/ directory).',
        },
        input: {
          type: 'string',
          description:
            'Input data or instructions to pass to the system.',
        },
      },
      required: ['system_name', 'input'],
    },
  },
];

const toolExecutors = {
  create_job: async (input) => {
    const result = await createJob(input.job_description);
    return {
      success: true,
      job_id: result.job_id,
      branch: result.branch,
    };
  },
  get_job_status: async (input) => {
    const result = await getJobStatus(input.job_id);
    return result;
  },
  list_templates: async (input) => {
    let templates = await getTemplates();
    if (input.query) {
      const q = input.query.toLowerCase();
      templates = templates.filter(t =>
        t.name.toLowerCase().includes(q) ||
        t.keywords.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)
      );
    }
    return { templates, count: templates.length };
  },
  run_system: async (input) => {
    const systems = await getSystemsCatalog();
    const system = systems.find(s => s.name === input.system_name);
    if (!system) {
      return {
        success: false,
        error: `System "${input.system_name}" not found. Available systems: ${systems.map(s => s.name).join(', ')}`,
      };
    }

    const jobDesc = [
      `Run the "${input.system_name}" system.`,
      '',
      `Read the system instructions at systems/${input.system_name}/CLAUDE.md and the workflow at systems/${input.system_name}/workflow.md.`,
      '',
      'Execute the system with the following input:',
      '',
      input.input,
    ].join('\n');

    const result = await createJob(jobDesc);
    return {
      success: true,
      job_id: result.job_id,
      branch: result.branch,
      system: input.system_name,
    };
  },
};

module.exports = { toolDefinitions, toolExecutors };
