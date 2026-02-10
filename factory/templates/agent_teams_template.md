## Parallel Execution — Native Agent Teams

This system uses Claude Code's native Agent Teams feature for parallel task execution. A **team lead** agent coordinates **teammate** agents that work concurrently on independent tasks.

**Environment requirement**: Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your environment.

---

### Team Structure

**Team Lead** — the primary agent running this workflow. Responsibilities:
- Create a shared task list for all parallel tasks
- Spawn teammate agents, each assigned to one independent task
- Monitor teammate progress via the shared task list
- Collect and merge results after all teammates complete
- Handle failures: retry failed tasks or fall back to sequential execution

**Teammates** — spawned agents that each own one task:

| Teammate | Task | Inputs | Expected Output |
|----------|------|--------|-----------------|
| {teammate_1_id} | {Task name} | {What this teammate receives} | {What this teammate produces} |
| {teammate_2_id} | {Task name} | {What this teammate receives} | {What this teammate produces} |
| {teammate_3_id} | {Task name} | {What this teammate receives} | {What this teammate produces} |

---

### Task Coordination

The team lead and teammates coordinate via the **shared task list**:

1. **Team lead creates tasks**:
   ```
   TaskCreate: subject="{task_name}", description="{scoped instructions}", activeForm="{Working on task_name}"
   ```
   Repeat for each parallel task. Set `blockedBy` if any task depends on another.

2. **Teammates claim and execute**:
   - Each teammate picks up its assigned task
   - Updates status: `pending` → `in_progress` (via TaskUpdate)
   - Executes the scoped work independently
   - Writes results to the designated output location
   - Updates status: `in_progress` → `completed` (via TaskUpdate)

3. **Team lead monitors and collects**:
   - Polls TaskList until all tasks show `completed`
   - Reads results from each teammate's output
   - Validates completeness and correctness
   - Merges results into the final output

4. **Failure handling**:
   - If a teammate fails, its task stays `in_progress` or gets flagged
   - Team lead detects the failure via TaskList
   - Team lead retries the failed task (sequentially) or generates a fallback result

---

### Display Modes

Agent Teams supports two display modes:

- **Default**: Compact summary showing each teammate's status on one line. Best for most workflows.
- **Verbose**: Full output from each teammate streamed as they work. Useful for debugging or monitoring complex tasks.

---

### Sequential Fallback

**If Agent Teams is not available** (environment variable not set or set to 0), execute all tasks sequentially in the order listed in the teammates table above.

The sequential path MUST produce identical results. The only difference is execution time:
- **Sequential**: Tasks run one after another. Total time ≈ sum of all task durations.
- **Parallel (Agent Teams)**: Independent tasks run simultaneously. Total time ≈ duration of the longest task.

Runtime check:
```
Check environment variable CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS.
If "1": use Agent Teams (team lead spawns teammates).
Otherwise: execute tasks sequentially in the listed order.
```

---

### Token Cost Note

Agent Teams uses additional tokens proportional to the number of teammates:
- **Sequential execution**: ~{X} tokens estimated (baseline)
- **Parallel execution**: ~{Y} tokens estimated ({N} teammates)
- Each teammate operates with its own context, so token usage scales roughly linearly
- **Tradeoff**: Faster execution for higher token cost. Use Agent Teams when speed matters more than cost.
