import axios from 'axios';

class Logger {
    constructor() {
        this.baseUrl = "https://logs-prod-020.grafana.net/loki/api/v1/push";
        this.userId = process.env.VUE_APP_GRAFANA_USER_ID;
        this.apiKey = process.env.VUE_APP_GRAFANA_TOKEN;
        
        // Create a dedicated axios instance for logging
        this.axiosInstance = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Basic ${btoa(`${this.userId}:${this.apiKey}`)}`,
                'X-Scope-OrgID': this.userId,
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Scope-OrgID'
            }
        });
    }

    async log(message, metadata = {}) {
        // If we're in development, just console log
        if (process.env.NODE_ENV === 'development') {
            console.log(`[${metadata.level || 'info'}]`, message, metadata);
            return;
        }

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

            await this.axiosInstance.post('', payload);
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