module.exports = {
  apps: [{
    name: 'freemobile-app',
    script: './start_app.sh',
    interpreter: '/bin/bash',
    cwd: '/home/ubuntu/FreeMobileApp',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '900M',
    env: {
      NODE_ENV: 'production',
      PORT: 8502
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
