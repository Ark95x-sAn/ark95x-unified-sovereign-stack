export type Phase = 'ready' | 'captured' | 'indexed' | 'routed' | 'drafted' | 'verified' | 'receipted';

export type Source = {
  id: string;
  name: string;
  excerpt: string;
};

export type AuditEvent = {
  step: string;
  actor: string;
  outcome: string;
};

export type Brief = {
  title: string;
  problem: string;
  proposal: string;
  openQuestions: string[];
  citations: string[];
};

export type Mission = {
  id: string;
  phase: Phase;
  audit: AuditEvent[];
  brief: Brief | null;
  verification: string | null;
  receipt: string | null;
};

export const sources: Source[] = [
  {
    id: 'F-01',
    name: 'sample_inquiry.txt',
    excerpt: 'A sample 12-unit property operator wants one place for tenant requests, maintenance status, and weekly updates. The operator asks for a pilot proposal. No budget or contact address is supplied.',
  },
  {
    id: 'F-02',
    name: 'sample_scope.txt',
    excerpt: 'A pilot could include a request intake form, a repair queue, and a weekly status report. The sample scope prohibits outbound messages during the demonstration.',
  },
];

export const fixtureBrief: Brief = {
  title: '12-unit property operations pilot',
  problem: 'The operator needs a single view of requests, repair status, and weekly updates. [F-01]',
  proposal: 'Draft a pilot with an intake form, repair queue, and weekly report. [F-02]',
  openQuestions: ['Budget and decision owner are missing. [F-01]', 'No contact address or authorized sender is supplied. [F-01]'],
  citations: ['F-01', 'F-02'],
};

export const phaseOrder: Phase[] = ['ready', 'captured', 'indexed', 'routed', 'drafted', 'verified', 'receipted'];

export const phaseLabels: Record<Phase, string> = {
  ready: 'Ready for intake',
  captured: '01 · Captured',
  indexed: '02 · Sources indexed',
  routed: '03 · Routed',
  drafted: '04 · Brief drafted',
  verified: '05 · Local guard passed',
  receipted: '06 · Demo review receipted',
};

export function createMission(): Mission {
  return { id: 'N95-DEMO-001', phase: 'ready', audit: [], brief: null, verification: null, receipt: null };
}

export function verifyBrief(brief: Brief, availableSources: Source[]): { pass: boolean; reason: string } {
  const known = new Set(availableSources.map((source) => source.id));
  const claims = [brief.problem, brief.proposal, ...brief.openQuestions];
  const text = claims.join(' ');
  if (!brief.title || !brief.problem || !brief.proposal || brief.openQuestions.length === 0) {
    return { pass: false, reason: 'Required brief fields are missing.' };
  }
  if (brief.citations.length === 0 || brief.citations.some((id) => !known.has(id))) {
    return { pass: false, reason: 'A citation has no source in the fixture.' };
  }
  const inText = Array.from(text.matchAll(/\[([A-Z]-\d+)\]/g), (match) => match[1]);
  if (inText.some((id) => !known.has(id) || !brief.citations.includes(id))) {
    return { pass: false, reason: 'A claim cites an unlisted or unavailable source.' };
  }
  if (claims.some((claim) => !/\[[A-Z]-\d+\]/.test(claim))) {
    return { pass: false, reason: 'A claim is missing its source reference.' };
  }
  if (brief.citations.some((id) => !text.includes(`[${id}]`))) {
    return { pass: false, reason: 'A listed source is not cited in the brief.' };
  }
  return { pass: true, reason: 'Required fields and source references match the local fixture.' };
}

export function advanceMission(mission: Mission, reviewerAcknowledged = false): Mission {
  if (mission.phase === 'receipted') return mission;
  if (mission.phase === 'verified' && !reviewerAcknowledged) return mission;

  const next = phaseOrder[phaseOrder.indexOf(mission.phase) + 1];
  if (!next || next === 'ready') return mission;
  const events: Record<Exclude<Phase, 'ready'>, AuditEvent> = {
    captured: { step: '01', actor: 'GM700 intake · simulated', outcome: 'Two sample files accepted into a local fixture.' },
    indexed: { step: '02', actor: 'Source index · simulated', outcome: 'F-01 and F-02 assigned source IDs.' },
    routed: { step: '03', actor: 'Net95X router · simulated', outcome: 'Brief lane assigned; all provider connections remain disconnected.' },
    drafted: { step: '04', actor: 'Local draft worker · simulated', outcome: 'Source-linked sample brief prepared; no external service was called.' },
    verified: { step: '05', actor: 'Separate local guard · fixture', outcome: 'Required fields and fixture source references checked. Independent agent review is planned.' },
    receipted: { step: '06', actor: 'Surface review · simulated', outcome: 'Demo review acknowledged; no device connection or signature occurred.' },
  };

  if (next === 'verified') {
    const result = verifyBrief(mission.brief ?? fixtureBrief, sources);
    if (!result.pass) return { ...mission, verification: `HELD: ${result.reason}` };
  }
  return {
    ...mission,
    phase: next,
    audit: [...mission.audit, events[next]],
    brief: next === 'drafted' ? { ...fixtureBrief } : mission.brief,
    verification: next === 'verified' ? 'PASS · local fixture references checked' : mission.verification,
    receipt: next === 'receipted' ? 'SIM-RECEIPT-N95-DEMO-001' : mission.receipt,
  };
}

export function attemptExternalSend(): { status: 'HELD'; reason: string } {
  return { status: 'HELD', reason: 'External sends are disabled in fixture mode. REV-002 remains held.' };
}
