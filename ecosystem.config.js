module.exports = {
  apps: [{
    name: 'freemobile-app',
    script: './start_app_production.sh',
    interpreter: '/bin/bash',
    cwd: '/home/freemobila/FreeMobileApp',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '900M',
    min_uptime: '10s',
    max_restarts: 10,
    env: {
      NODE_ENV: 'production',
      PORT: 8502,
      ADDRESS: '0.0.0.0'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    merge_logs: true,
    kill_timeout: 5000
  }]
};
