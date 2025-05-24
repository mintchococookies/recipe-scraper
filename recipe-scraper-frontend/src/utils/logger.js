import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: 'https://logs-prod-020.grafana.net/loki/api/v1/push',
    headers: {
        'Content-Type': 'application/json'
    }
});

class Logger {
    constructor() {
        this.userId = process.env.VUE_APP_GRAFANA_USER_ID;
        this.apiKey = process.env.VUE_APP_GRAFANA_TOKEN;
    }

    async log(message, metadata = {}) {
        // If we're in development, just console log
        if (process.env.NODE_ENV === 'development') {
            console.log(`[${metadata.level || 'info'}]`, message, metadata);
            return;
        }

        try {
            const timestamp = new Date().getTime();
            const payload = {
                app: 'recipe-scraper-frontend',
                environment: process.env.NODE_ENV || 'development',
                timestamp,
                message,
                ...metadata
            };

            await axiosInstance.post('', payload, {
                auth: {
                    username: this.userId,
                    password: this.apiKey
                }
            });
        } catch (error) {
            // In case of logging failure, fallback to console
            console.error('Failed to send logs to Grafana:', error);
            console.log(`[${metadata.level || 'info'}] ${message}`, metadata);
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