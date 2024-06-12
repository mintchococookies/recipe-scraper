<template>
  <div id="app">
    <noscript>
      <strong>We're sorry but recipe-scraper-frontend doesn't work properly without JavaScript enabled. Please enable it
        to continue.</strong>
    </noscript>
    <div v-if="isLoggedIn">
      <p>DEBUG: Login successful</p>
    </div>
    <LoginComponent v-else @logged-in="fetchProtectedData" />
    <div v-if="isLoggedIn">
      <input type="text" v-model="recipeUrl" placeholder="Enter recipe URL" />
      <button @click="submitRecipeUrl">Submit Recipe URL</button>
      <div v-if="recipeResponse">
        <div class="recipe-name">
          <h2>{{ recipeResponse.recipe_name }}</h2>
        </div>
        <div class="recipe-ingredients">
          <p><strong>Ingredients:</strong></p>
          <ul>
            <li v-for="(ingredient, index) in recipeResponse.ingredients" :key="index">{{ ingredient }}</li>
          </ul>
          <button @click="convertUnits">{{ unitType === 'metric' ? 'Convert to SI' : 'Convert to Metric' }}</button>
        </div>
        <div class="recipe-steps">
          <p><strong>Steps:</strong></p>
          <ol>
            <li v-for="(step, index) in recipeResponse.recipe_steps" :key="index">{{ step }}</li>
          </ol>
        </div>
        <div class="recipe-servings">
          <p><strong>Servings:</strong> {{ servingSize }}</p>
          <div>
            <label for="servingSize">Serving Size:</label>
            <input type="number" id="servingSize" v-model.number="servingSizeInput" min="1" max="100">
            <button @click="updateServingSize">Update Serving Size</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import LoginComponent from './components/LoginComponent.vue';

export default {
  name: 'App',
  components: {
    LoginComponent
  },
  data() {
    return {
      isLoggedIn: false,
      recipeUrl: '',
      recipeResponse: null,
      unitType: null,
      servingSize: null,
      servingSizeInput: null
    };
  },
  methods: {
    async fetchProtectedData() {
      try {
        const token = localStorage.getItem('jwt_token');
        const response = await axios.get('http://127.0.0.1:5000/test-protected', {
          headers: {
            Authorization: `${token}`
          }
        });
        this.responseData = response.data.message;
      } catch (error) {
        console.error('Error fetching data:', error.response ? error.response.data : error.message);
      }
    },
    async submitRecipeUrl() {
      try {
        const token = localStorage.getItem('jwt_token');
        if (!token) {
          console.error('No token found');
          return;
        }
        const response = await axios.post('http://127.0.0.1:5000/scrape-recipe-steps', {
          recipe_url: this.recipeUrl
        }, {
          headers: {
            Authorization: `${token}`
          }
        });
        this.recipeResponse = response.data;
        // Initialize unitType to original_unit_type
        this.unitType = this.recipeResponse.original_unit_type;
        this.servingSize = this.recipeResponse.servings;
        this.servingSizeInput = this.recipeResponse.servings;
      } catch (error) {
        console.error('Error submitting recipe URL:', error.response ? error.response.data : error.message);
      }
    },
    async convertUnits() {
      try {
        const token = localStorage.getItem('jwt_token');
        if (!token) {
          console.error('No token found');
          return;
        }
        const temp_unit = this.unitType === 'metric' ? 'si' : 'metric';
        const response = await axios.post('http://127.0.0.1:5000/convert-recipe-units', {
          unit_type: temp_unit,
          ingredients: this.recipeResponse.ingredients
        }, {
          headers: {
            Authorization: `${token}`
          }
        });
        this.recipeResponse.ingredients = response.data;
        // Swap button text after successful conversion
        this.unitType = this.unitType === 'metric' ? 'si' : 'metric';
      } catch (error) {
        console.error('Error converting units:', error.response ? error.response.data : error.message);
      }
    },
    async updateServingSize() {
      try {
        const token = localStorage.getItem('jwt_token');
        if (!token) {
          console.error('No token found');
          return;
        }
        const response = await axios.post('http://127.0.0.1:5000/calculate-serving-ingredients', {
          serving_size: this.servingSizeInput
        }, {
          headers: {
            Authorization: `${token}`
          }
        });
        // Update ingredients based on API response
        this.recipeResponse.ingredients = response.data;
        // Update servingSize after successful update
        this.servingSize = this.servingSizeInput;
      } catch (error) {
        console.error('Error calculating ingredients:', error.response ? error.response.data : error.message);
      }
    }
  },
  mounted() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      this.isLoggedIn = true;
    }
  }
};
</script>

<style>
/* Add any custom styles here */
.recipe-name {
  margin-bottom: 10px;
}

.recipe-ingredients,
.recipe-steps,
.recipe-servings {
  margin-top: 10px;
}
</style>
