import axios from 'axios';

class Logger {
    constructor() {
        this.baseUrl = "https://logs-prod-020.grafana.net/loki/api/v1/push";
        this.userId = process.env.VUE_APP_GRAFANA_USER_ID;
        this.apiKey = process.env.VUE_APP_GRAFANA_TOKEN;
    }

    async log(message, metadata = {}) {
        try {
            const timestamp = new Date().getTime() * 1e9; // Convert to nanoseconds
            const labels = {
                app: 'recipe-scraper-frontend',
                environment: process.env.NODE_ENV || 'development',
                ...metadata
            };

            const payload = {
                streams: [
                    {
                        stream: labels,
                        values: [
                            [timestamp.toString(), message]
                        ]
                    }
                ]
            };

            await axios.post(this.baseUrl, payload, {
                auth: {
                    username: this.userId,
                    password: this.apiKey
                },
                headers: {
                    'Content-Type': 'application/json',
                }
            });
        } catch (error) {
            console.error('Failed to send logs to Grafana:', error);
        }
    }

    // Helper methods for different log levels
    info(message, metadata = {}) {
        return this.log(message, { ...metadata, level: 'info' });
    }

    error(message, metadata = {}) {
        return this.log(message, { ...metadata, level: 'error' });
    }

    warn(message, metadata = {}) {
        return this.log(message, { ...metadata, level: 'warn' });
    }

    debug(message, metadata = {}) {
        return this.log(message, { ...metadata, level: 'debug' });
    }
}

export const logger = new Logger();

// Vue plugin installation
export default {
    install: (app) => {
        app.config.globalProperties.$logger = logger;
    }
};