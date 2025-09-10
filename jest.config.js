module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/server/**/*.test.js'],
  collectCoverage: true,
  collectCoverageFrom: [
    'server/**/*.js',
    '!server/**/jobs/**',
    '!server/**/config/**',
    '!server/**/index.js'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov']
};

