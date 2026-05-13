export const en = {
  brand: {
    name: 'AI Career Intelligence',
    subtitle: 'Intelligent Career Decision Platform',
  },
  nav: {
    reset: 'Reset',
    quickRun: 'Quick Analysis',
    running: 'Analyzing...',
    demoBadge: 'DEMO',
  },
  hero: {
    title: 'Intelligent Career Decision Platform',
    description:
      'AI-powered career profiling, job recommendations, strategy generation, and path simulation to help you make optimal career decisions.',
    startBtn: 'Start Analysis',
  },
  status: {
    generated: 'Generated',
    elapsed: 'Elapsed',
    candidates: 'Candidates',
    version: 'Version',
    demoMode: 'Demo Mode — Mock Data',
  },
  actOne: {
    title: 'Career Profile',
    subtitle: 'Input your goals and let the system parse and recommend',
    inputLabel: 'Describe your career goals, skills, and experience',
    inputPlaceholder: 'e.g. Goal: Senior Backend Engineer, skills: Python, FastAPI...',
    runBtn: 'Run Analysis',
    runningBtn: 'Analysis Running...',
    experience: 'Experience',
    education: 'Education',
    skillsParsed: 'Skills Parsed',
    locations: 'Locations',
    parsedSkills: 'Parsed Skills',
    careerGoals: 'Career Goals',
    yearSuffix: 'y',
  },
  actTwo: {
    title: 'Strategy Recommendations',
    subtitle: 'Multi-dimensional scoring and strategy optimization',
    topStrategies: 'Top Strategies',
    offPathWarning: 'Off-Path Warning',
    rlWeights: 'Optimization Weights',
    rlIteration: 'Iter',
    severity: {
      high: 'HIGH',
      medium: 'MED',
      low: 'LOW',
    },
  },
  actThree: {
    title: 'Simulation Validation',
    subtitle: 'Simulate career development paths and decision processes',
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
    title: 'Analysis Progress',
    logTitle: 'analysis.log',
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
