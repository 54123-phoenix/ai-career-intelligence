export const zh = {
  brand: {
    name: 'AI Career Intelligence',
    subtitle: '多智能体决策系统',
  },
  nav: {
    reset: '重置',
    quickRun: '快速运行',
    running: '运行中...',
    demoBadge: '演示模式',
  },
  hero: {
    title: '战略职业决策系统',
    description:
      '6 智能体流水线：解析 → 检索 → 评审 → 架构 → 模拟 → 前端。基于强化学习的策略生成与多智能体模拟验证。',
    startBtn: '开始演示',
  },
  status: {
    execution: '执行ID',
    generated: '生成时间',
    pipeline: '流水线',
    elapsed: '耗时',
    candidates: '候选策略',
    version: '版本',
    demoMode: '演示模式 — Mock 数据',
  },
  actOne: {
    title: '第一幕 — 职业画像',
    subtitle: '输入您的目标，让智能体完成解析、检索与评审',
    inputLabel: '描述您的职业目标、技能和经验',
    inputPlaceholder: '例如：目标成为高级后端工程师，掌握 Python、FastAPI...',
    runBtn: '运行智能分析',
    runningBtn: '流水线运行中...',
    experience: '工作经验',
    education: '学历',
    skillsParsed: '解析技能',
    locations: '期望地点',
    parsedSkills: '已解析技能',
    careerGoals: '职业目标',
    yearSuffix: '年',
  },
  actTwo: {
    title: '第二幕 — 策略战场',
    subtitle: '多智能体评分 + 强化学习优化权重',
    topStrategies: 'Top 策略',
    offPathWarning: '偏离路径警告',
    rlWeights: '强化学习权重',
    rlIteration: '迭代',
    severity: {
      high: '高',
      medium: '中',
      low: '低',
    },
  },
  actThree: {
    title: '第三幕 — 模拟验证',
    subtitle: '多智能体模拟：候选人 vs HR vs 市场',
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
    title: '流水线执行',
    agents: {
      parser: {
        name: '解析智能体',
        desc: '解析职业目标与技能...',
      },
      retrieval: {
        name: '检索智能体',
        desc: '匹配职位与策略...',
      },
      reviewer: {
        name: '评审智能体',
        desc: '评分与排序策略...',
      },
      architect: {
        name: '架构智能体',
        desc: '构建职业规划与时间线...',
      },
      simulator: {
        name: '模拟智能体',
        desc: '运行多智能体模拟...',
      },
      frontend: {
        name: '前端智能体',
        desc: '渲染可视化数据...',
      },
    },
    logTitle: 'agent-pipeline.log',
    done: '完成',
    running: '运行中',
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
