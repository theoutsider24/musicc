// Karma configuration
const puppeteer = require('puppeteer');
process.env.CHROME_BIN = puppeteer.executablePath();

module.exports = function (config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: 'musicc',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine', 'browserify'],


    // list of files / patterns to load in the browser
    files: [
      'static/js/lib/jquery-3.4.1.js',
      'static/js/lib/jquery-ui.js',
      'static/js/lib/jsonform/deps/underscore.js',
      'static/js/lib/jsonform/lib/jsonform.js',
      'static/js/search/main.js',
      'static/js/search/resultTable.js',
      'static/js/search/searchbar.js',
      'static/js/search/sidebar.js',
      'static/js/common/json.js',
      'static/js/common/toasts.js',
      'static/js/common/tools.js',
      'tests/js/**/*[sS]pec.js'
    ],


    // list of files to exclude
    exclude: [
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      'static/js/!(lib)/*.js': ['coverage'],
      'tests/js/**/*[sS]pec.js': ['browserify']
    },


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress', 'coverage'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['HeadlessChrome'],
    customLaunchers: {
      HeadlessChrome: {
        base: 'ChromeHeadless',
        flags: ['--no-sandbox']
      }
    },

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: true,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity,
    coverageReporter: {
      dir: '../test_artefacts',
      reporters: [
        { type: 'lcov', subdir: './js_coverage' },
        { type: 'text-summary' },
        { type: 'clover', subdir: './js_clover', file: 'clover.xml' }
      ]
    }
  })
}