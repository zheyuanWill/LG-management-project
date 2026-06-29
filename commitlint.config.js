export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新功能
        'fix',      // 修复
        'docs',     // 文档
        'style',    // 格式（不影响代码运行的变动）
        'refactor', // 重构
        'perf',     // 性能优化
        'test',     // 测试
        'build',    // 构建系统或外部依赖项的更改
        'ci',       // CI 配置
        'chore',    // 其他修改
        'revert',   // 回滚
        'wip'       // 开发中
      ]
    ],
    'subject-case': [0],
    'subject-full-stop': [0]
  }
}

