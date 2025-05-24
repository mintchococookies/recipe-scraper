import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: 'https://logs-prod-020.grafana.net/loki/api/v1/push',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.VUE_APP_GRAFANA_USER_ID}:${process.env.VUE_APP_GRAFANA_TOKEN}`
    }
});

class Logger {
    async log(message, metadata = {}) {
        try {
            const timestamp = Date.now() * 1000000; // Convert to nanoseconds
            const payload = {
                streams: [{
                    stream: {
                        app: 'recipe-scraper-frontend',
                        level: metadata.level || 'info',
                        ...metadata
                    },
                    values: [[timestamp.toString(), message]]
                }]
            };

            await axiosInstance.post('', payload);
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