<template>
  <div id="app">
    <noscript>
      <strong>We're sorry but recipe-scraper-frontend doesn't work properly without JavaScript enabled. Please enable it
        to continue.</strong>
    </noscript>
    <div v-if="isLoggedIn">
      <p>DEBUG: Login successful</p>
    </div>
    <LoginComponent />
    <div v-if="isLoggedIn">
      <input type="text" v-model="recipeUrl" placeholder="Enter recipe URL" />
      <button @click="submitRecipeUrl">Submit Recipe URL</button>
      <!-- Display error message if present -->
      <div v-if="recipeResponse && recipeResponse.error" class="error-message">
        <p>{{ recipeResponse.error }}</p>
      </div>
      <div v-else-if="recipeResponse">
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
    <!-- Disclaimer -->
    <div class="disclaimer">
      <p>We ❤ Recipes (and Code), but sometimes they don't see eye to eye!</p>
      <p>The web is a wonderful (and sometimes wacky) place, and every website has its own unique way of presenting
        things. We've done our best to train our recipe detectives to handle all sorts of situations, but occasionally
        they might encounter a website that throws them a curveball.</p>
      <p>If you ever find a recipe that doesn't seem quite right, don't be shy! Just send us a quick email at
        xxx@gmail.com and we'll be happy to put on our detective hats and see if we can fix it.</p>
      <p>Thanks for your understanding, and happy cooking! ‍‍</p>
    </div>
    <!-- Current Limitations -->
    <div class="limitations">
      <h3>Current Limitations:</h3>
      <ul>
        <li>All unit conversions involving cups are based on the density of water (for liquids) and flour (for solids) as
          a proof of concept. More accurate conversions based on specific ingredients have yet to be implemented. It's
          important to consider the density of ingredients when converting units, as the conversion
          factor may vary
          depending on the type of ingredient being measured. For instance, while the metric system suggests 250 grams in
          1 cup, this value can differ based on the density of the ingredient. In the meantime, you can find a
          comprehensive list of conversions for different ingredients from the web: <a
            href="https://www.allrecipes.com/article/cup-to-gram-conversions/">https://www.allrecipes.com/article/cup-to-gram-conversions/</a>
        </li>
      </ul>
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
      servingSizeInput: null,
      token: null
    };
  },
  methods: {
    async submitRecipeUrl() {
      try {
        if (!this.isLoggedIn) {
          console.error('No token found');
          return;
        }
        const response = await axios.post('http://127.0.0.1:5000/scrape-recipe-steps', {
          recipe_url: this.recipeUrl
        }, {
          headers: {
            Authorization: `${this.token}`
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
        if (!this.isLoggedIn) {
          console.error('No token found');
          return;
        }
        const temp_unit = this.unitType === 'metric' ? 'si' : 'metric';
        const response = await axios.post('http://127.0.0.1:5000/convert-recipe-units', {
          unit_type: temp_unit,
          ingredients: this.recipeResponse.ingredients
        }, {
          headers: {
            Authorization: `${this.token}`
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
        if (!this.isLoggedIn) {
          console.error('No token found');
          return;
        }
        const response = await axios.post('http://127.0.0.1:5000/calculate-serving-ingredients', {
          serving_size: this.servingSizeInput
        }, {
          headers: {
            Authorization: `${this.token}`
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
    this.token = token;
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
