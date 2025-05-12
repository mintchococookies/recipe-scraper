<template>
    <p style="display:none;"></p>
</template>
<script>
import axios from 'axios';

export default {
    name: 'LoginComponent',
    data() {
        return {
            isLoggedIn: false,
            apiUrl: process.env.VUE_APP_API_URL,
            retryAttempts: 0,
            maxRetryAttempts: 5,
            retryDelay: 500 // Delay between retry attempts in milliseconds
        };
    },
    async mounted() {
        await this.tryLogin();
    },
    methods: {
        async tryLogin() {
            while (!this.isLoggedIn && this.retryAttempts < this.maxRetryAttempts) {
                try {
                    const response = await axios.post(`${this.apiUrl}/login`, {
                        username: process.env.VUE_APP_USERNAME,
                        password: process.env.VUE_APP_PASSWORD
                    });
                    const token = response.data.token;
                    localStorage.setItem('jwt_token', token);
                    this.isLoggedIn = true;
                    this.$emit('logged-in');
                } catch (error) {
                    console.error('Login attempt failed:', error);
                    this.retryAttempts++;
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                }
            }

            if (!this.isLoggedIn) {
                console.error('Max retry attempts reached. Login failed.');
            }
        }
    }
};
</script>