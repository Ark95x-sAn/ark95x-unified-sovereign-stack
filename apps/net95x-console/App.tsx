import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaProvider, useSafeAreaInsets } from 'react-native-safe-area-context';
import { advanceMission, attemptExternalSend, createMission, phaseLabels, phaseOrder, sources, type Mission, type Phase } from './src/mission';

type Screen = 'Command' | 'Queue' | 'Proof' | 'Agency' | 'Review';
type NavItem = { name: Screen; glyph: string; caption: string };

const NAV: NavItem[] = [
  { name: 'Command', glyph: '⌘', caption: 'Aim point' },
  { name: 'Queue', glyph: '▦', caption: 'Work register' },
  { name: 'Proof', glyph: '◈', caption: 'Evidence' },
  { name: 'Agency', glyph: '◎', caption: 'Crew & devices' },
  { name: 'Review', glyph: '✓', caption: 'Decision gate' },
];

const C = {
  ink: '#0B1525', navy: '#101E32', panel: '#172940', panel2: '#1B3049',
  line: '#2A4058', soft: '#9AACC0', white: '#F4F7F5', teal: '#6CE0CB',
  lime: '#D2E77E', amber: '#F9C879', rose: '#F4A6A1', blue: '#78B8F6',
};

const crew = [
  { name: 'ChatGPT Dot', role: 'Voice intake', history: 'Conversation handoff' },
  { name: 'ChatGPT Pro', role: 'Decision synthesis', history: 'Strategy history' },
  { name: 'Ollama', role: 'Local draft lane', history: 'Caller-held records' },
  { name: 'Codex A / B', role: 'Build / independent review', history: 'Code and check receipts' },
  { name: 'Perplexity + Grok', role: 'Research / challenge', history: 'Source trails' },
  { name: 'Groq', role: 'Fast extraction', history: 'Caller-held logs' },
  { name: 'M365 Copilot + Office Agent', role: 'Business context / editable files', history: 'Accessible tenant records' },
  { name: 'Copilot Cowork', role: 'Workflow coordination', history: 'Permitted handoffs' },
  { name: 'Windows Copilot', role: 'Desktop guidance', history: 'Confirmed fixes' },
  { name: 'OpenClaw Companion + Web', role: 'Operator view / browser lane', history: 'Available task traces' },
  { name: 'Meta AI + Muse', role: 'Signals / follow-up proposals', history: 'Provider-held context' },
];

const devices = [
  { number: '17', title: 'Surface Pro X', role: 'Review console', detail: 'Review decisions and receipts', glyph: '▰' },
  { number: '16', title: 'RTX 2080 PC', role: 'Compute delegate', detail: 'Optional workload worker', glyph: '⬡' },
  { number: '15', title: 'GM700 · SOLARISX', role: 'Operations core', detail: 'Register, index, router, receipts', glyph: '◫' },
];

function Label({ children, color = C.teal }: { children: React.ReactNode; color?: string }) {
  return <Text style={[s.label, { color }]}>{children}</Text>;
}

function Pill({ children, tone = 'teal' }: { children: React.ReactNode; tone?: 'teal' | 'amber' | 'rose' | 'blue' }) {
  const color = { teal: C.teal, amber: C.amber, rose: C.rose, blue: C.blue }[tone];
  return <View style={[s.pill, { borderColor: color + '55', backgroundColor: color + '15' }]}><Text style={[s.pillText, { color }]}>{children}</Text></View>;
}

function Button({ title, onPress, secondary = false, disabled = false, small = false }: {
  title: string; onPress: () => void; secondary?: boolean; disabled?: boolean; small?: boolean;
}) {
  return (
    <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress}
      style={({ pressed }) => [s.button, secondary && s.buttonSecondary, small && s.buttonSmall, disabled && s.buttonDisabled, pressed && !disabled && { opacity: 0.75 }]}>
      <Text style={[s.buttonText, secondary && s.buttonSecondaryText, disabled && { color: C.soft }]}>{title}</Text>
    </Pressable>
  );
}

function Panel({ children, style }: { children: React.ReactNode; style?: any }) {
  return <View style={[s.panel, style]}>{children}</View>;
}

function SectionHead({ eyebrow, title, aside }: { eyebrow: string; title: string; aside?: string }) {
  return <View style={s.sectionHead}><View><Label>{eyebrow}</Label><Text style={s.sectionTitle}>{title}</Text></View>{aside ? <Text style={s.sectionAside}>{aside}</Text> : null}</View>;
}

function SideNav({ current, setScreen }: { current: Screen; setScreen: (screen: Screen) => void }) {
  return (
    <View style={s.sidebar}>
      <View style={s.brand}><View style={s.brandMark}><Text style={s.brandMarkText}>N</Text></View><View><Text style={s.brandTitle}>NET95X</Text><Text style={s.brandSubtitle}>AGENCY CONSOLE</Text></View></View>
      <View style={s.sidebarDivider} />
      <Label color={C.soft}>WORKSPACE</Label>
      <View style={s.sideLinks}>{NAV.map((item) => (
        <Pressable key={item.name} onPress={() => setScreen(item.name)} accessibilityRole="button" style={[s.sideLink, current === item.name && s.sideLinkActive]}>
          <Text style={[s.sideGlyph, current === item.name && { color: C.teal }]}>{item.glyph}</Text><Text style={[s.sideName, current === item.name && { color: C.white }]}>{item.name}</Text>
          {current === item.name && <View style={s.activeDot} />}
        </Pressable>
      ))}</View>
      <View style={s.sidebarBottom}><Label color={C.amber}>ENVIRONMENT</Label><Text style={s.sidebarBottomTitle}>Simulation only</Text><Text style={s.sidebarBottomCopy}>No provider, device, or account connections. External sends held.</Text><View style={s.statusLine}><View style={s.warningDot} /><Text style={s.statusLineText}>OFFLINE FIXTURE</Text></View></View>
    </View>
  );
}

function BottomNav({ current, setScreen }: { current: Screen; setScreen: (screen: Screen) => void }) {
  const insets = useSafeAreaInsets();
  return <View style={[s.bottomNav, { height: 67 + insets.bottom, paddingBottom: insets.bottom }]}>{NAV.map((item) => <Pressable key={item.name} accessibilityRole="button" onPress={() => setScreen(item.name)} style={s.bottomItem}>
    <Text style={[s.bottomGlyph, current === item.name && { color: C.teal }]}>{item.glyph}</Text><Text style={[s.bottomLabel, current === item.name && { color: C.white }]}>{item.name}</Text>
  </Pressable>)}</View>;
}

function Flow({ phase }: { phase: Phase }) {
  const stages = [
    { phase: 'captured', title: 'Intake', subtitle: 'Sample folder' },
    { phase: 'indexed', title: 'Index', subtitle: 'F-01 · F-02' },
    { phase: 'routed', title: 'Route', subtitle: 'Local lane' },
    { phase: 'drafted', title: 'Draft', subtitle: 'Cited brief' },
    { phase: 'verified', title: 'Check', subtitle: 'Local guard' },
    { phase: 'receipted', title: 'Receipt', subtitle: 'Surface review' },
  ] as const;
  const current = phaseOrder.indexOf(phase);
  return <View style={s.flow}>{stages.map((step, index) => {
    const complete = current >= index + 1;
    const active = current === index;
    return <View key={step.phase} style={s.flowItem}><View style={[s.flowNode, complete && s.flowNodeDone, active && s.flowNodeActive]}><Text style={[s.flowNumber, complete && { color: C.ink }]}>{complete ? '✓' : String(index + 1)}</Text></View><Text style={[s.flowTitle, complete && { color: C.white }]}>{step.title}</Text><Text style={s.flowSubtitle}>{step.subtitle}</Text></View>;
  })}</View>;
}

function Command({ mission, onAdvance, setScreen, compact }: { mission: Mission; onAdvance: () => void; setScreen: (screen: Screen) => void; compact: boolean }) {
  const title: Record<Phase, string> = {
    ready: 'Start fixture intake', captured: 'Index sample sources', indexed: 'Route the brief', routed: 'Draft source-linked brief',
    drafted: 'Run local guard', verified: 'Open review gate', receipted: 'View completed receipt',
  };
  const action = () => mission.phase === 'verified' ? setScreen('Review') : mission.phase === 'receipted' ? setScreen('Proof') : onAdvance();
  return <>
    <View style={[s.hero, compact && s.heroCompact]}><View style={s.heroGlowOne} /><View style={s.heroGlowTwo} />
      <View style={{ flex: 1, zIndex: 1 }}><Label color={C.lime}>COMMAND / SIX-STAGE DEMO</Label><Text style={[s.heroTitle, compact && s.heroTitleCompact]}>One aim point.{ '\n' }A checked outcome.</Text><Text style={s.heroCopy}>Take a sample business folder through a source-linked brief, a local guard check, and a simulated Surface review receipt.</Text>
        <View style={s.heroActions}><Button title={title[mission.phase] + '  →'} onPress={action} /><Button title="See work queue" secondary onPress={() => setScreen('Queue')} /></View>
      </View>
      {!compact && <View style={s.heroOrb}><Text style={s.heroOrbTop}>NET95X</Text><Text style={s.heroOrbGlyph}>✦</Text><Text style={s.heroOrbBottom}>CONTROL LAYER</Text></View>}
    </View>
    <View style={s.gridTwo}><Panel style={s.gridMajor}><SectionHead eyebrow="ACTIVE MISSION" title="Sample property operations brief" aside="N95-DEMO-001" /><Text style={s.body}>A fictional 12-unit property operator needs a pilot for tenant requests, repair tracking, and weekly status. Budget and decision owner are absent from the source folder.</Text>
      <View style={s.metaRow}><Pill>{phaseLabels[mission.phase]}</Pill><Pill tone="amber">FIXTURE DATA</Pill><Pill tone="blue">2 SOURCES</Pill></View><View style={s.divider} /><Flow phase={mission.phase} /></Panel>
      <Panel style={s.gridMinor}><SectionHead eyebrow="OPERATING LIMITS" title="Control status" /><View style={s.limitRow}><View style={s.limitIcon}><Text style={s.limitIconText}>↗</Text></View><View style={{ flex: 1 }}><Text style={s.limitTitle}>External actions held</Text><Text style={s.limitCopy}>The REV-002 send freeze is represented as a hard hold. This demo never transmits.</Text></View></View><View style={s.divider} /><View style={s.limitRow}><View style={[s.limitIcon, { backgroundColor: C.blue + '18' }]}><Text style={[s.limitIconText, { color: C.blue }]}>⌁</Text></View><View style={{ flex: 1 }}><Text style={s.limitTitle}>Connectors disconnected</Text><Text style={s.limitCopy}>AI providers, Windows controls, and all three PCs are planning records here.</Text></View></View><View style={s.divider} /><Text style={s.smallNote}>No case documents, personal histories, or account exports are included.</Text></Panel>
    </View>
    <SectionHead eyebrow="THE NEXT HANDOFF" title="What the console will produce" /><View style={s.tileGrid}><MiniTile number="01" title="A cited brief" copy="Every claim points back to the supplied sample files." accent={C.teal} /><MiniTile number="02" title="A checked result" copy="A separate local guard confirms required fields and source IDs; independent agent review is planned." accent={C.blue} /><MiniTile number="03" title="A review receipt" copy="Acknowledge the demo on the simulated Surface review screen." accent={C.lime} /></View>
  </>;
}

function MiniTile({ number, title, copy, accent }: { number: string; title: string; copy: string; accent: string }) {
  return <View style={s.miniTile}><Text style={[s.miniNumber, { color: accent }]}>{number}</Text><Text style={s.miniTitle}>{title}</Text><Text style={s.miniCopy}>{copy}</Text></View>;
}

function Queue({ mission, setScreen }: { mission: Mission; setScreen: (screen: Screen) => void }) {
  return <><SectionHead eyebrow="QUEUE / LOCAL REGISTER" title="One mission, one current state" aside="Fixture work only" /><Panel><View style={s.queueTop}><View><Label color={C.soft}>PRIORITY 01 · CASH-FIRST DEMO</Label><Text style={s.queueTitle}>Sample business folder → service brief</Text><Text style={s.queueCopy}>Owner: Net95X local simulator  ·  Review target: Surface Pro X (simulated)</Text></View><Pill>{phaseLabels[mission.phase]}</Pill></View><View style={s.divider} /><View style={s.queueColumns}><InfoStat value="2" label="SOURCE FILES" /><InfoStat value={`${mission.audit.length}/6`} label="STAGES RECORDED" /><InfoStat value="0" label="EXTERNAL CALLS" /></View><View style={s.queueActions}><Button title="Open task proof  →" small onPress={() => setScreen('Proof')} /><Button title="Advance at command" small secondary onPress={() => setScreen('Command')} /></View></Panel>
    <View style={s.spacer} /><SectionHead eyebrow="SOURCE REGISTER" title="Supplied sample folder" /><View style={s.gridTwo}>{sources.map((source) => <Panel key={source.id} style={s.gridHalf}><View style={s.sourceTop}><Text style={s.sourceId}>{source.id}</Text><Pill tone="amber">SAMPLE</Pill></View><Text style={s.sourceName}>{source.name}</Text><Text style={s.sourceExcerpt}>{source.excerpt}</Text></Panel>)}</View>
    <View style={s.notice}><Text style={s.noticeTitle}>History stays with its source</Text><Text style={s.noticeCopy}>Specialist histories are future adapter provenance. This fixture contains no imported account conversations.</Text></View>
  </>;
}

function InfoStat({ value, label }: { value: string; label: string }) { return <View style={s.infoStat}><Text style={s.infoValue}>{value}</Text><Text style={s.infoLabel}>{label}</Text></View>; }

function Proof({ mission, setScreen }: { mission: Mission; setScreen: (screen: Screen) => void }) {
  return <><SectionHead eyebrow="TASK / N95-DEMO-001" title="Proof before completion" aside={phaseLabels[mission.phase]} />
    <View style={s.gridTwo}><Panel style={s.gridMajor}><View style={s.sourceTop}><Label>OUTPUT ARTIFACT</Label><Pill tone={mission.brief ? 'teal' : 'amber'}>{mission.brief ? 'DRAFT READY' : 'AWAITING STAGE 04'}</Pill></View>
      <Text style={s.proofTitle}>{mission.brief?.title ?? 'Source-linked brief pending'}</Text>{mission.brief ? <><Field label="THE NEED" value={mission.brief.problem} /><Field label="PROPOSED PILOT" value={mission.brief.proposal} /><Field label="OPEN QUESTIONS" value={mission.brief.openQuestions.join('\n')} /><View style={s.citations}>{mission.brief.citations.map((id) => <Pill key={id} tone="blue">[{id}] SOURCE</Pill>)}</View></> : <Text style={s.body}>Run stages 01 through 04 from the Command screen. The brief appears here with references to the two fixture files.</Text>}
    </Panel><Panel style={s.gridMinor}><SectionHead eyebrow="CHECK & RECEIPT" title="Acceptance state" /><GateRow label="Source references" state={mission.brief ? 'LINKED' : 'WAITING'} color={mission.brief ? C.teal : C.amber} /><GateRow label="Local guard" state={mission.verification ?? 'WAITING'} color={mission.verification?.startsWith('PASS') ? C.teal : C.amber} /><GateRow label="Surface review" state={mission.receipt ?? 'WAITING'} color={mission.receipt ? C.teal : C.amber} /><View style={s.divider} /><Text style={s.smallNote}>Independent agent verification is planned. This receipt is a simulation marker; no physical Surface connection or live signature occurred.</Text><View style={{ marginTop: 20 }}><Button title="Go to review gate  →" secondary onPress={() => setScreen('Review')} /></View></Panel></View>
    <View style={s.spacer} /><SectionHead eyebrow="EVENT LOG" title="Every transition leaves a trace" /><Panel>{mission.audit.length ? mission.audit.map((event, index) => <View key={event.step} style={[s.auditRow, index > 0 && { borderTopWidth: 1, borderTopColor: C.line }]}><Text style={s.auditStep}>{event.step}</Text><View style={{ flex: 1 }}><Text style={s.auditActor}>{event.actor}</Text><Text style={s.auditOutcome}>{event.outcome}</Text></View><Text style={s.auditTick}>✓</Text></View>) : <Text style={s.body}>No events yet. Start stage 01 from Command.</Text>}</Panel>
  </>;
}

function Field({ label, value }: { label: string; value: string }) { return <View style={s.field}><Label color={C.soft}>{label}</Label><Text style={s.fieldValue}>{value}</Text></View>; }
function GateRow({ label, state, color }: { label: string; state: string; color: string }) { return <View style={s.gateRow}><Text style={s.gateLabel}>{label}</Text><Text style={[s.gateValue, { color }]}>{state}</Text></View>; }

function Agency({ compact }: { compact: boolean }) {
  return <><SectionHead eyebrow="AGENCY / CONNECTION MAP" title="A crew with defined lanes" aside="All integrations planned" />
    <View style={s.agencyBanner}><Text style={s.agencyBannerGlyph}>◎</Text><View style={{ flex: 1 }}><Text style={s.agencyBannerTitle}>One local task record. Specialist context by source.</Text><Text style={s.agencyBannerCopy}>Member histories remain with their products until an export or adapter is verified. The console would pass only task-relevant excerpts with provenance.</Text></View></View>
    <SectionHead eyebrow="15—17 / HARDWARE" title="Desktop topology" /><View style={[s.deviceGrid, compact && { flexDirection: 'column' }]}>{devices.map((device) => <Panel key={device.number} style={s.deviceCard}><View style={s.sourceTop}><Text style={s.deviceGlyph}>{device.glyph}</Text><Pill tone="amber">DISCONNECTED</Pill></View><Text style={s.deviceNumber}>{device.number} / {device.role.toUpperCase()}</Text><Text style={s.deviceTitle}>{device.title}</Text><Text style={s.deviceCopy}>{device.detail}</Text></Panel>)}</View>
    <View style={s.spacer} /><SectionHead eyebrow="1—14 · 18—19 / SPECIALISTS" title="Proposed agent assignments" /><View style={s.crewGrid}>{crew.map((member) => <View key={member.name} style={s.crewCard}><View style={s.crewDot} /><View style={{ flex: 1 }}><Text style={s.crewName}>{member.name}</Text><Text style={s.crewRole}>{member.role}</Text><Text style={s.crewHistory}>History: {member.history} · adapter pending</Text></View></View>)}</View><Text style={s.smallNote}>Slot 2 remains unassigned. No capability is inferred from the presence of a named product.</Text>
  </>;
}

function Review({ mission, onReview, setScreen }: { mission: Mission; onReview: () => void; setScreen: (screen: Screen) => void }) {
  const canReview = mission.phase === 'verified';
  const isDone = mission.phase === 'receipted';
  const send = attemptExternalSend();
  return <><SectionHead eyebrow="REVIEW / STAGE 06" title="Human decision point" aside="Surface Pro X · simulated" />
    <View style={s.gridTwo}><Panel style={s.gridMajor}><View style={s.reviewEmblem}><Text style={s.reviewEmblemText}>{isDone ? '✓' : '◈'}</Text></View><Label color={C.lime}>SAMPLE BRIEF REVIEW</Label><Text style={s.reviewTitle}>{isDone ? 'Demo receipt recorded.' : canReview ? 'The brief is ready for your review.' : 'Complete the upstream checks first.'}</Text><Text style={s.body}>{isDone ? `Receipt ${mission.receipt} records an in-app simulated acknowledgement. No physical Surface connection, signature, or external submission occurred.` : canReview ? 'The fixture brief has references to F-01 and F-02 and a local guard pass. Open proof, then record a demonstration acknowledgement.' : 'Run intake, source indexing, routing, drafting, and the local guard on the Command screen.'}</Text><View style={s.reviewActions}><Button title={isDone ? 'View receipt  →' : 'Inspect task proof  →'} onPress={() => setScreen('Proof')} secondary /><Button title={isDone ? 'Receipt recorded' : 'Record demo review  →'} onPress={onReview} disabled={!canReview} /></View></Panel>
    <Panel style={s.gridMinor}><SectionHead eyebrow="EXTERNAL ACTION GATE" title="Outbound is held" /><View style={s.heldBox}><Text style={s.heldGlyph}>⌁</Text><Text style={s.heldTitle}>{send.status} · REV-002</Text><Text style={s.heldCopy}>{send.reason}</Text></View><View style={s.divider} /><GateRow label="Provider connections" state="DISCONNECTED" color={C.amber} /><GateRow label="Device confirmation" state="UNVERIFIED" color={C.amber} /><GateRow label="External send" state="HELD" color={C.rose} /><Text style={[s.smallNote, { marginTop: 18 }]}>The control is hard coded for fixture mode. There is no network send function in this app.</Text></Panel></View>
  </>;
}

function Console() {
  const [screen, setScreen] = useState<Screen>('Command');
  const [mission, setMission] = useState<Mission>(createMission);
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const compact = width < 860;
  const advance = () => setMission((current) => advanceMission(current));
  const review = () => setMission((current) => advanceMission(current, true));
  return <View style={[s.app, { paddingTop: insets.top, paddingLeft: insets.left, paddingRight: insets.right }]}>
    {!compact && <SideNav current={screen} setScreen={setScreen} />}
    <View style={s.main}><View style={s.topbar}><View><Text style={s.topbarEyebrow}>NETWORK‑95 / OPERATOR WORKSPACE</Text><Text style={s.topbarTitle}>{screen}</Text></View><View style={s.topbarRight}><View style={s.topbarDot} /><Text style={s.topbarStatus}>FIXTURE MODE</Text>{!compact && <Text style={s.topbarSession}>SESSION · LOCAL DEMO</Text>}</View></View>
      <ScrollView contentContainerStyle={[s.content, compact && s.contentCompact]}>
        {screen === 'Command' && <Command mission={mission} onAdvance={advance} setScreen={setScreen} compact={compact} />}
        {screen === 'Queue' && <Queue mission={mission} setScreen={setScreen} />}
        {screen === 'Proof' && <Proof mission={mission} setScreen={setScreen} />}
        {screen === 'Agency' && <Agency compact={compact} />}
        {screen === 'Review' && <Review mission={mission} onReview={review} setScreen={setScreen} />}
        <View style={s.footer}><Text style={s.footerMark}>N95X · SYNTHETIC SYNERGETIC AGENCY</Text><Text style={s.footerCopy}>Prototype · No live agents, imports, device commands, or sends</Text></View>
      </ScrollView>
      {compact && <BottomNav current={screen} setScreen={setScreen} />}
    </View>
  </View>;
}

export default function App() {
  return <SafeAreaProvider style={{ flex: 1, backgroundColor: C.ink }}><Console /></SafeAreaProvider>;
}

const s = StyleSheet.create({
  app: { flex: 1, minHeight: '100%', flexDirection: 'row', backgroundColor: C.ink },
  sidebar: { width: 232, backgroundColor: C.navy, paddingHorizontal: 23, paddingTop: 28, borderRightWidth: 1, borderRightColor: C.line },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 11 }, brandMark: { width: 38, height: 38, backgroundColor: C.teal, borderRadius: 11, alignItems: 'center', justifyContent: 'center' }, brandMarkText: { fontSize: 24, fontWeight: '900', color: C.ink }, brandTitle: { fontSize: 18, fontWeight: '900', letterSpacing: 2, color: C.white }, brandSubtitle: { color: C.soft, fontWeight: '700', fontSize: 9, letterSpacing: 1.6, marginTop: 2 },
  sidebarDivider: { height: 1, backgroundColor: C.line, marginVertical: 28 }, label: { fontWeight: '900', fontSize: 10, letterSpacing: 2 }, sideLinks: { gap: 5, marginTop: 15 }, sideLink: { height: 47, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 13, borderRadius: 11, gap: 14 }, sideLinkActive: { backgroundColor: C.panel2 }, sideGlyph: { width: 20, fontSize: 19, textAlign: 'center', color: C.soft }, sideName: { color: C.soft, fontSize: 13, fontWeight: '700' }, activeDot: { width: 5, height: 5, backgroundColor: C.teal, borderRadius: 3, marginLeft: 'auto' },
  sidebarBottom: { marginTop: 'auto', marginBottom: 28, padding: 15, backgroundColor: C.panel, borderRadius: 14, borderWidth: 1, borderColor: C.line }, sidebarBottomTitle: { color: C.white, fontSize: 14, fontWeight: '800', marginTop: 9 }, sidebarBottomCopy: { color: C.soft, fontSize: 11, lineHeight: 17, marginTop: 7 }, statusLine: { flexDirection: 'row', alignItems: 'center', gap: 7, marginTop: 16 }, warningDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: C.amber }, statusLineText: { color: C.amber, fontSize: 10, fontWeight: '900', letterSpacing: 1 },
  main: { flex: 1, minWidth: 0 }, topbar: { minHeight: 84, borderBottomWidth: 1, borderBottomColor: C.line, paddingHorizontal: 36, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 }, topbarEyebrow: { color: C.soft, fontSize: 9, fontWeight: '900', letterSpacing: 1.7 }, topbarTitle: { color: C.white, fontSize: 22, fontWeight: '800', marginTop: 4 }, topbarRight: { flexDirection: 'row', alignItems: 'center', gap: 7 }, topbarDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: C.amber }, topbarStatus: { color: C.amber, fontSize: 10, letterSpacing: 1, fontWeight: '900' }, topbarSession: { color: C.soft, borderLeftWidth: 1, borderLeftColor: C.line, paddingLeft: 17, marginLeft: 12, fontSize: 10, fontWeight: '700' },
  content: { width: '100%', maxWidth: 1450, alignSelf: 'center', paddingHorizontal: 36, paddingVertical: 30, gap: 22, paddingBottom: 54 }, contentCompact: { paddingHorizontal: 17, paddingVertical: 18, paddingBottom: 35 },
  hero: { overflow: 'hidden', borderRadius: 20, minHeight: 302, backgroundColor: '#19453F', borderWidth: 1, borderColor: '#388375', padding: 32, flexDirection: 'row', alignItems: 'center' }, heroCompact: { minHeight: 300, padding: 23 }, heroGlowOne: { position: 'absolute', width: 380, height: 380, borderRadius: 190, backgroundColor: '#23665B', right: -110, top: -140 }, heroGlowTwo: { position: 'absolute', width: 210, height: 210, borderRadius: 110, backgroundColor: '#2A7666', right: 115, bottom: -160 }, heroTitle: { color: C.white, fontSize: 42, lineHeight: 47, fontWeight: '900', letterSpacing: -1.5, marginTop: 14 }, heroTitleCompact: { fontSize: 33, lineHeight: 37 }, heroCopy: { color: '#C9E6DA', fontSize: 14, lineHeight: 21, maxWidth: 610, marginTop: 13 }, heroActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 25 }, heroOrb: { width: 200, height: 200, borderRadius: 100, borderWidth: 1, borderColor: '#A0F3DC66', alignItems: 'center', justifyContent: 'center', backgroundColor: '#B0F3DA14', marginRight: 25 }, heroOrbTop: { color: '#C9E6DA', fontSize: 12, fontWeight: '900', letterSpacing: 4 }, heroOrbGlyph: { color: C.lime, fontSize: 82, lineHeight: 104 }, heroOrbBottom: { color: '#C9E6DA', fontSize: 9, fontWeight: '900', letterSpacing: 2 },
  button: { minHeight: 44, borderRadius: 9, paddingHorizontal: 18, paddingVertical: 12, backgroundColor: C.lime, alignItems: 'center', justifyContent: 'center' }, buttonSecondary: { backgroundColor: 'transparent', borderColor: '#BDE7D9', borderWidth: 1 }, buttonSmall: { minHeight: 38, paddingVertical: 9 }, buttonDisabled: { opacity: 0.45 }, buttonText: { color: C.ink, fontWeight: '900', fontSize: 12, letterSpacing: 0.1 }, buttonSecondaryText: { color: C.white },
  panel: { backgroundColor: C.panel, borderRadius: 16, padding: 22, borderWidth: 1, borderColor: C.line }, gridTwo: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 }, gridMajor: { flexGrow: 2, flexBasis: 480, minWidth: 0 }, gridMinor: { flexGrow: 1, flexBasis: 290, minWidth: 0 }, gridHalf: { flexGrow: 1, flexBasis: 310, minWidth: 0 }, sectionHead: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 15, flexWrap: 'wrap', marginBottom: 8 }, sectionTitle: { color: C.white, fontSize: 20, fontWeight: '800', marginTop: 7, letterSpacing: -0.3 }, sectionAside: { color: C.soft, fontSize: 11, fontWeight: '700' }, body: { color: '#BFCDDB', fontSize: 13, lineHeight: 21, marginTop: 14 }, metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 20 }, pill: { borderWidth: 1, paddingHorizontal: 9, paddingVertical: 6, borderRadius: 6, alignSelf: 'flex-start' }, pillText: { fontSize: 9, fontWeight: '900', letterSpacing: 0.8 }, divider: { height: 1, backgroundColor: C.line, marginVertical: 20 },
  flow: { flexDirection: 'row', flexWrap: 'wrap', gap: 13, justifyContent: 'space-between' }, flowItem: { minWidth: 70, flexGrow: 1, flexBasis: 70, alignItems: 'center' }, flowNode: { width: 32, height: 32, borderRadius: 16, borderWidth: 1, borderColor: C.line, backgroundColor: C.navy, alignItems: 'center', justifyContent: 'center' }, flowNodeActive: { borderColor: C.lime }, flowNodeDone: { backgroundColor: C.teal, borderColor: C.teal }, flowNumber: { color: C.soft, fontSize: 12, fontWeight: '900' }, flowTitle: { color: C.soft, fontSize: 11, fontWeight: '800', marginTop: 9 }, flowSubtitle: { color: C.soft, fontSize: 9, marginTop: 4, textAlign: 'center' },
  limitRow: { flexDirection: 'row', gap: 12, marginTop: 17 }, limitIcon: { width: 35, height: 35, borderRadius: 9, alignItems: 'center', justifyContent: 'center', backgroundColor: C.rose + '18' }, limitIconText: { color: C.rose, fontSize: 18, fontWeight: '800' }, limitTitle: { color: C.white, fontSize: 13, fontWeight: '800' }, limitCopy: { color: C.soft, fontSize: 11, lineHeight: 17, marginTop: 5 }, smallNote: { color: C.soft, fontSize: 11, lineHeight: 17 }, tileGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 13 }, miniTile: { flexGrow: 1, flexBasis: 230, padding: 19, borderRadius: 13, backgroundColor: C.navy, borderWidth: 1, borderColor: C.line }, miniNumber: { fontWeight: '900', fontSize: 12, letterSpacing: 2 }, miniTitle: { color: C.white, fontSize: 15, fontWeight: '800', marginTop: 14 }, miniCopy: { color: C.soft, fontSize: 11, lineHeight: 17, marginTop: 7 },
  queueTop: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: 15 }, queueTitle: { color: C.white, fontWeight: '800', fontSize: 19, marginTop: 12 }, queueCopy: { color: C.soft, fontSize: 12, marginTop: 8, lineHeight: 18 }, queueColumns: { flexDirection: 'row', flexWrap: 'wrap', gap: 14 }, infoStat: { flexGrow: 1, flexBasis: 100 }, infoValue: { fontSize: 25, fontWeight: '900', color: C.white }, infoLabel: { color: C.soft, fontSize: 9, fontWeight: '900', letterSpacing: 1, marginTop: 5 }, queueActions: { flexDirection: 'row', gap: 10, marginTop: 23, flexWrap: 'wrap' }, spacer: { height: 4 }, sourceTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 }, sourceId: { color: C.teal, fontWeight: '900', fontSize: 11, letterSpacing: 1.5 }, sourceName: { color: C.white, fontSize: 16, fontWeight: '800', marginTop: 12 }, sourceExcerpt: { color: C.soft, fontSize: 12, lineHeight: 19, marginTop: 10 }, notice: { padding: 18, borderRadius: 12, borderColor: '#405267', borderWidth: 1, backgroundColor: C.navy }, noticeTitle: { color: C.white, fontSize: 12, fontWeight: '800' }, noticeCopy: { color: C.soft, fontSize: 11, lineHeight: 18, marginTop: 5 },
  proofTitle: { color: C.white, fontSize: 23, fontWeight: '900', marginTop: 20 }, field: { marginTop: 22 }, fieldValue: { color: '#D1DCE4', fontSize: 13, lineHeight: 21, marginTop: 9 }, citations: { flexDirection: 'row', gap: 7, marginTop: 24 }, gateRow: { paddingVertical: 13, borderBottomWidth: 1, borderBottomColor: C.line, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 }, gateLabel: { color: C.soft, fontSize: 11, flex: 1 }, gateValue: { fontSize: 10, fontWeight: '900', textAlign: 'right', flexShrink: 1 }, auditRow: { flexDirection: 'row', alignItems: 'center', gap: 15, paddingVertical: 13 }, auditStep: { color: C.teal, fontSize: 12, fontWeight: '900', width: 26 }, auditActor: { color: C.white, fontSize: 12, fontWeight: '800' }, auditOutcome: { color: C.soft, fontSize: 11, lineHeight: 17, marginTop: 4 }, auditTick: { color: C.teal, fontSize: 17 },
  agencyBanner: { padding: 22, borderWidth: 1, borderColor: '#456E75', backgroundColor: '#1D3D4A', borderRadius: 14, flexDirection: 'row', gap: 17, alignItems: 'center' }, agencyBannerGlyph: { fontSize: 34, color: C.teal }, agencyBannerTitle: { color: C.white, fontWeight: '800', fontSize: 15 }, agencyBannerCopy: { color: '#BBD2D8', fontSize: 11, lineHeight: 17, marginTop: 7 }, deviceGrid: { flexDirection: 'row', gap: 13 }, deviceCard: { flex: 1, minWidth: 0 }, deviceGlyph: { fontSize: 24, color: C.teal }, deviceNumber: { color: C.soft, fontSize: 10, letterSpacing: 1, fontWeight: '900', marginTop: 22 }, deviceTitle: { color: C.white, fontSize: 16, fontWeight: '900', marginTop: 7 }, deviceCopy: { color: C.soft, fontSize: 11, lineHeight: 17, marginTop: 8 }, crewGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 11 }, crewCard: { flexDirection: 'row', gap: 12, padding: 15, backgroundColor: C.panel, borderWidth: 1, borderColor: C.line, borderRadius: 11, flexGrow: 1, flexBasis: 270 }, crewDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: C.amber, marginTop: 5 }, crewName: { color: C.white, fontSize: 12, fontWeight: '800' }, crewRole: { color: C.teal, fontSize: 11, marginTop: 5 }, crewHistory: { color: C.soft, fontSize: 10, lineHeight: 15, marginTop: 7 },
  reviewEmblem: { width: 54, height: 54, borderRadius: 15, backgroundColor: C.teal + '1C', alignItems: 'center', justifyContent: 'center', marginBottom: 22 }, reviewEmblemText: { color: C.teal, fontSize: 27, fontWeight: '800' }, reviewTitle: { color: C.white, fontSize: 24, fontWeight: '900', marginTop: 13, lineHeight: 31 }, reviewActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 30 }, heldBox: { backgroundColor: C.rose + '12', borderColor: C.rose + '55', borderWidth: 1, borderRadius: 11, padding: 17, marginTop: 20 }, heldGlyph: { color: C.rose, fontSize: 26 }, heldTitle: { color: C.rose, fontSize: 13, fontWeight: '900', marginTop: 8 }, heldCopy: { color: '#D9B8B8', fontSize: 11, lineHeight: 17, marginTop: 7 },
  footer: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 8, borderTopWidth: 1, borderTopColor: C.line, paddingTop: 19, marginTop: 9 }, footerMark: { color: C.teal, fontSize: 9, letterSpacing: 1, fontWeight: '900' }, footerCopy: { color: C.soft, fontSize: 10 },
  bottomNav: { height: 67, flexDirection: 'row', backgroundColor: C.navy, borderTopColor: C.line, borderTopWidth: 1 }, bottomItem: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 3 }, bottomGlyph: { fontSize: 21, color: C.soft }, bottomLabel: { color: C.soft, fontSize: 9, fontWeight: '800' },
});
