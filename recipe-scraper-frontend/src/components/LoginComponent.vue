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
            isLoggedIn: false
        };
    },
    async mounted() {
        await this.login();
    },
    methods: {
        async login() {
            try {
                const response = await axios.post('http://127.0.0.1:5000/login', {
                    username: 'user',
                    password: 'pw'
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
  