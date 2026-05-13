export const zh = {
  brand: {
    name: 'AI Career Intelligence',
    subtitle: '智能职业决策平台',
  },
  nav: {
    reset: '重置',
    quickRun: '快速分析',
    running: '分析中...',
    demoBadge: '演示模式',
  },
  hero: {
    title: '智能职业决策平台',
    description:
      '基于 AI 的职业画像解析、岗位推荐、发展策略生成与路径模拟验证，助您做出最优职业决策。',
    startBtn: '开始分析',
  },
  status: {
    generated: '生成时间',
    elapsed: '耗时',
    candidates: '候选策略',
    version: '版本',
    demoMode: '演示模式 — Mock 数据',
  },
  actOne: {
    title: '职业画像',
    subtitle: '输入您的目标，系统将自动解析并推荐',
    inputLabel: '描述您的职业目标、技能和经验',
    inputPlaceholder: '例如：目标成为高级后端工程师，技能：Python、FastAPI...',
    runBtn: '运行智能分析',
    runningBtn: '分析进行中...',
    experience: '工作经验',
    education: '学历',
    skillsParsed: '解析技能',
    locations: '期望地点',
    parsedSkills: '已解析技能',
    careerGoals: '职业目标',
    yearSuffix: '年',
  },
  actTwo: {
    title: '策略推荐',
    subtitle: '多维度评分与策略优化',
    topStrategies: '推荐策略',
    offPathWarning: '偏离路径警告',
    rlWeights: '优化权重',
    rlIteration: '迭代',
    severity: {
      high: '高',
      medium: '中',
      low: '低',
    },
  },
  actThree: {
    title: '模拟验证',
    subtitle: '模拟职业发展路径与决策过程',
    avgSuccessRate: '平均成功率',
    totalRounds: '总轮次',
    passed: '通过',
    failed: '失败',
    heatmapTitle: '逐轮热力图',
    aggregatedRisks: '聚合风险',
    skillGaps: '暴露技能缺口',
    strategyDiversity: '策略多样性',
    overfittingRisk: '过拟合风险',
  },
  pipeline: {
    title: '分析进度',
    logTitle: 'analysis.log',
    done: '完成',
    running: '进行中',
  },
  drawer: {
    description: '描述',
    strategyNote: '策略建议',
    riskWarning: '风险提示',
  },
  common: {
    close: '关闭',
    confirm: '确认',
    cancel: '取消',
  },
} as const;

export type Zh = typeof zh;
