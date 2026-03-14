const assert = require("assert");
const path = require("path");

const {
  DEFAULT_COMMAND_TIMEOUT_MS,
  createActiveCommandTracker,
  execCommand,
  normalizeValidationCommand,
} = require("./validation_runtime");

async function testExecCommandTimesOut() {
  const result = await execCommand("sleep 2", process.cwd(), { timeoutMs: 50 });
  assert.strictEqual(result.code, 124);
  assert.strictEqual(result.timedOut, true);
  assert.strictEqual(result.timeoutMs, 50);
}

function testTrackerRestartsOnlyWhenStale() {
  let now = 10_000;
  let killed = 0;
  const tracker = createActiveCommandTracker({ now: () => now });
  const child = {
    kill() {
      killed += 1;
    },
  };

  tracker.trackChild("validate", child);
  let result = tracker.restartIfStale(20_000);
  assert.strictEqual(result.restarted, false);
  assert.strictEqual(killed, 0);

  now = 40_500;
  result = tracker.restartIfStale(20_000);
  assert.strictEqual(result.restarted, true);
  assert.strictEqual(result.label, "validate");
  assert(result.elapsedMs >= 30_000);
  assert.strictEqual(killed, 1);

  tracker.clearChild(child);
  assert.strictEqual(tracker.snapshot(), null);
}

function testNormalizeValidationCommand() {
  assert.strictEqual(
    normalizeValidationCommand("uv run python scripts/validate_canonical.py --check-changes --json"),
    "uv run python scripts/validate_canonical.py --check-changes"
  );
  assert.strictEqual(
    normalizeValidationCommand("uv run python scripts/validate_canonical.py --json"),
    "uv run python scripts/validate_canonical.py"
  );
  assert.strictEqual(
    normalizeValidationCommand("uv run python scripts/other.py --json"),
    "uv run python scripts/other.py --json"
  );
}

async function main() {
  assert(DEFAULT_COMMAND_TIMEOUT_MS >= 60_000);
  await testExecCommandTimesOut();
  testTrackerRestartsOnlyWhenStale();
  testNormalizeValidationCommand();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
