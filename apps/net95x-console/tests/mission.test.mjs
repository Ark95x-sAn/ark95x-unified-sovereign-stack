import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { advanceMission, attemptExternalSend, createMission, fixtureBrief, sources, verifyBrief } from '../src/mission.ts';

test('six fixture phases advance in order, record a source-linked brief, and require review acknowledgement', () => {
  let mission = createMission();
  for (const phase of ['captured', 'indexed', 'routed', 'drafted', 'verified']) {
    mission = advanceMission(mission);
    assert.equal(mission.phase, phase);
  }
  assert.deepEqual(mission.brief?.citations, ['F-01', 'F-02']);
  assert.match(mission.verification, /^PASS/);
  assert.equal(advanceMission(mission), mission);
  mission = advanceMission(mission, true);
  assert.equal(mission.phase, 'receipted');
  assert.equal(mission.receipt, 'SIM-RECEIPT-N95-DEMO-001');
  assert.deepEqual(mission.audit.map((event) => event.step), ['01', '02', '03', '04', '05', '06']);
});

test('verifier rejects unsupported source IDs and missing fields', () => {
  assert.deepEqual(verifyBrief({ ...fixtureBrief, citations: ['F-99'] }, sources), {
    pass: false,
    reason: 'A citation has no source in the fixture.',
  });
  assert.equal(verifyBrief({ ...fixtureBrief, proposal: '' }, sources).pass, false);
  assert.equal(verifyBrief({ ...fixtureBrief, proposal: 'Unsupported claim. [F-99]' }, sources).pass, false);
  assert.equal(verifyBrief({ ...fixtureBrief, problem: 'An uncited need.' }, sources).pass, false);
});

test('external send remains held with no state mutation', () => {
  const mission = createMission();
  assert.equal(attemptExternalSend().status, 'HELD');
  assert.equal(mission.phase, 'ready');
});

test('displayed source excerpts match bundled sample files', () => {
  for (const source of sources) {
    const file = readFileSync(new URL(`../fixtures/${source.name}`, import.meta.url), 'utf8');
    assert.ok(file.includes(source.excerpt), `${source.id} diverged from its fixture file`);
  }
});
