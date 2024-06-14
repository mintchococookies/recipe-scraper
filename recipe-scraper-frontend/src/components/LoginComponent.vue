<template>
    <div>
        <button v-if="!isLoggedIn" disabled>Logging in...</button>
    </div>
</template>
  
<script>
import axios from 'axios';

export default {
    name: 'LoginComponent',
    data() {
        return {
            isLoggedIn: false,
            apiUrl: process.env.VUE_APP_API_URL
        };
    },
    async mounted() {
        await this.login();
    },
    methods: {
        async login() {
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
                console.error('Login failed:', error);
            }
        }
    }
};
</script>
  