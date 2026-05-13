export const en = {
  brand: {
    name: 'AI Career Intelligence',
    subtitle: 'Multi-Agent Decision System',
  },
  nav: {
    reset: 'Reset',
    quickRun: 'Quick Run',
    running: 'Running...',
    demoBadge: 'DEMO',
  },
  hero: {
    title: 'Strategic Career Decision System',
    description:
      '6-agent pipeline: Parse → Retrieve → Review → Architect → Simulate → Frontend. RL-optimized strategy generation with multi-agent simulation validation.',
    startBtn: 'Start Demonstration',
  },
  status: {
    execution: 'Execution',
    generated: 'Generated',
    pipeline: 'Pipeline',
    elapsed: 'Elapsed',
    candidates: 'Candidates',
    version: 'Version',
    demoMode: 'Demo Mode — Mock Data',
  },
  actOne: {
    title: 'Act I — Career Profile',
    subtitle: 'Input your goals and let agents parse, retrieve, and review',
    inputLabel: 'Describe your career goals, skills, and experience',
    inputPlaceholder: 'e.g. Goal: Senior Backend Engineer, skills: Python, FastAPI...',
    runBtn: 'Run Intelligence',
    runningBtn: 'Pipeline Running...',
    experience: 'Experience',
    education: 'Education',
    skillsParsed: 'Skills Parsed',
    locations: 'Locations',
    parsedSkills: 'Parsed Skills',
    careerGoals: 'Career Goals',
    yearSuffix: 'y',
  },
  actTwo: {
    title: 'Act II — Strategy Battlefield',
    subtitle: 'Multi-agent scoring + RL-optimized weights',
    topStrategies: 'Top Strategies',
    offPathWarning: 'Off-Path Warning',
    rlWeights: 'RL Weights',
    rlIteration: 'Iter',
    severity: {
      high: 'HIGH',
      medium: 'MED',
      low: 'LOW',
    },
  },
  actThree: {
    title: 'Act III — Simulation Validation',
    subtitle: 'Multi-agent simulation: Candidate vs HR vs Market',
    avgSuccessRate: 'Avg Success Rate',
    totalRounds: 'Total Rounds',
    passed: 'Passed',
    failed: 'Failed',
    heatmapTitle: 'Round-by-Round Heatmap',
    aggregatedRisks: 'Aggregated Risks',
    skillGaps: 'Skill Gaps Exposed',
    strategyDiversity: 'Strategy Diversity',
    overfittingRisk: 'Overfitting Risk',
  },
  pipeline: {
    title: 'Pipeline Execution',
    agents: {
      parser: {
        name: 'Parser Agent',
        desc: 'Parsing career goals & skills...',
      },
      retrieval: {
        name: 'Retrieval Agent',
        desc: 'Matching jobs & strategies...',
      },
      reviewer: {
        name: 'Reviewer Agent',
        desc: 'Scoring & ranking strategies...',
      },
      architect: {
        name: 'Architect Agent',
        desc: 'Building career plan & timeline...',
      },
      simulator: {
        name: 'Simulator Agent',
        desc: 'Running multi-agent simulation...',
      },
      frontend: {
        name: 'Frontend Agent',
        desc: 'Rendering visualization...',
      },
    },
    logTitle: 'agent-pipeline.log',
    done: 'DONE',
    running: 'RUNNING',
  },
  drawer: {
    description: 'Description',
    strategyNote: 'Strategy Note',
    riskWarning: 'Risk Warning',
  },
  common: {
    close: 'Close',
    confirm: 'Confirm',
    cancel: 'Cancel',
  },
} as const;

export type En = typeof en;
