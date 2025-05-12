<template>
  <div id="app">
    <LoginComponent />
    <main>
      <h1>&#129386; Recipe Scraper</h1>
      <div id="input-div">
        <input type="text" v-model="recipeUrl" placeholder="Paste recipe URL" />
        <button id="submit-button" :disabled="loading" @click="submitRecipeUrl">{{ loading ? 'Loading..' : 'Search'
        }}</button>
      </div>
      <div v-if="isLoggedIn">
        <!-- Display error message if api returns error -->
        <div v-if="recipeResponse && recipeResponse.error" class="error-message">
          <p>{{ recipeResponse.error }}</p>
        </div>
        <div id="main-content" v-else-if="recipeResponse">
          <div class="recipe-name">
            <h2>{{ recipeResponse.recipe_name }}</h2>
          </div>
          <p id="hidden-source">Source: {{ recipeUrl }}</p>
          <div class="recipe-servings">
            <h3 class="part-heading"><strong>🥣 Servings:</strong></h3><input type="number" id="servingSize"
              v-model.number="servingSizeInput" min="1" max="100"><button @click="updateServingSize"
              id="servings-button">Calculate</button>
          </div>
          <div class="recipe-ingredients" v-if="recipeResponse.ingredients">
            <div class="ingredients-flex">
              <h3 class="part-heading"><strong>📜 Ingredients:</strong></h3><button @click="convertUnits"
                id="convert-button">{{ unitType ===
                  'metric' ? 'Convert to SI' : 'Convert to Metric' }}</button>
            </div>
            <div v-for="(ingredient, index) in recipeResponse.ingredients" :key="index" class="recipe-ingredient">
              <input type="checkbox" :id="'ingredient-' + index" />
              <label :for="'ingredient-' + index">{{ ingredient.join(' ') }}</label>
            </div>
          </div>
          <div v-else>
            <p><strong>Ingredients:</strong> Not available</p>
          </div>
          <div class="recipe-steps">
            <h3 class="part-heading"><strong>🐾 Steps:</strong></h3>
            <div v-for="(step, index) in recipeResponse.recipe_steps" :key="index" class="recipe-step">
              <input type="checkbox" :id="'step-' + index" />
              <span class="recipe-step-number">{{ index + 1 }}.</span>
              <label :for="'step-' + index">{{ step }}</label>
            </div>
          </div>
          <div id="print-button-div"><button @click="printPage">Print Recipe</button></div>
        </div>
      </div>
      <p id="refresh-disclaimer">
        <i>The app's API is hosted on a free deployment server which may experience cold starts. Please refresh the
          page if
          nothing happens. Thank you for your understanding!</i>
      </p>
      <div class="bottom-stuff">
        <div class="disclaimer">
          <h2>We ❤ Recipes (and code), but sometimes they don't see eye to eye! 🧐</h2>
          <p>The web is a wonderful (and sometimes wacky) place, and every website has its own unique way of presenting
            things. We've done our best to train our recipe detectives to handle all sorts of website layouts, but
            occasionally
            they might encounter one that throws them a curveball.</p>
          <p>If you ever find a recipe that doesn't seem quite right, don't be shy! Just drop us a quick message at
            <a href="https://mintchococookies.com/">mintchococookies.com</a> and we'll be happy to put on our detective
            hats
            and see if
            we can fix it. 🕵🏻‍♀️
          </p>
          <p>Thanks for your understanding, and happy cooking! 👩🏻‍🍳 ‍‍</p>
        </div>
        <div class="limitations">
          <h3>Current Limitations:</h3>
          <ul>
            <li>All unit conversions involving cups are based on the density of water (for liquids) and flour (for solids)
              as
              a proof of concept. More accurate conversions based on the density of specific ingredients have yet to be
              implemented. In the meantime, you can find a
              comprehensive list of conversions for different ingredients from the web: <a
                href="https://www.allrecipes.com/article/cup-to-gram-conversions/">Cups to Grams Conversions</a>
            </li>
          </ul>
        </div>
      </div>

    </main>
    <div class="footer">
      <p>© Lilian 2024 | Created with Flask, BeautifulSoup & Vue JS </p>
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Poppins:wght@500;700&display=swap');

#refresh-disclaimer {
  padding-top: 1rem;
  padding-bottom: 1rem;
  font-size: 80%;
  margin: 0 auto;
  text-align: center;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.footer {
  font-size: 0.75rem;
  bottom: 0;
  margin: 0 auto;
  text-align: center;
}

body {
  font-family: 'JetBrains Mono', monospace;
  background-color: #0A1828;
  color: #fff;
}

main {
  flex: 1;
  margin: 0 auto;
  padding-top: 2rem;
  padding-bottom: 2rem;
  width: 50%;
}

h1 {
  font-weight: 800;
}

.recipe-name {
  margin-bottom: 10px;
}

.recipe-ingredients,
.recipe-steps,
.recipe-servings {
  margin-top: 10px;
}

.recipe-servings,
.ingredients-flex {
  display: flex;
  align-items: center;
  gap: 20px;
}

.recipe-steps,
.recipe-ingredients {
  display: flex;
  flex-direction: column;
}

.recipe-step,
.recipe-ingredient {
  display: flex;
  align-items: flex-start;
  margin-bottom: 10px;
}

.recipe-step input[type="checkbox"],
.recipe-ingredient input[type="checkbox"] {
  margin-right: 20px;
  width: 18px;
  height: 18px;
}

.recipe-step-number {
  margin-right: 10px;
}

.recipe-step label,
.recipe-ingredient label {
  flex: 1;
}

#input-div {
  display: flex;
  justify-content: space-between;
  padding-bottom: 3rem;
  padding-top: 1.5rem;
  height: 4vh;
}

input[type="text"] {
  width: 70%;
  height: 100%;
  padding: 0 15px;
  font-size: 15px;
  border: 1px solid #F5F5F5;
  border-radius: 5px;
  outline: none;
  font-family: 'JetBrains Mono', monospace;
  background: #F5F5F5;
}

input[type="number"] {
  padding: 4px 0px 4px 10px;
  font-size: 17px;
  font-weight: 600;
  border: 2px solid #F5F5F5;
  border-radius: 5px;
  outline: none;
  font-family: 'JetBrains Mono', monospace;
  background: #0A1828;
  height: 100%;
  color: #F5F5F5;
}

input[type="checkbox"] {
  width: 40px;
}

button {
  font-family: 'JetBrains Mono', monospace;
  border: none;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 5px;
  font-weight: 600;
  font-size: 15px;
  text-decoration: none;
  height: 100%;
  transition: background-color 0.4s ease;
}

button:active {
  background-color: #afeeee;
}

.part-heading {
  font-weight: 800;
}

#servings-button,
#convert-button {
  font-family: 'JetBrains Mono', monospace;
  border: none;
  cursor: pointer;
  background-color: #0A1828;
  border: 2px solid #F5F5F5;
  padding: 6px 10px;
  border-radius: 5px;
  font-weight: bold;
  text-decoration: none;
  height: 100%;
  color: #F5F5F5;
}

#submit-button {
  width: 20%;
}

#servings-button,
#convert-button {
  transition: background-color 0.3s ease;
}

#servings-button:active,
#convert-button:active {
  background-color: #ccc;
}

.disclaimer {
  font-size: 90%;
}

.limitations {
  padding-top: 1rem;
  font-size: 90%;
}

a {
  color: #afeeee;
  font-weight: 600;
}

.recipe-name>h2 {
  font-weight: 1000;
  text-decoration: underline;
}

#print-button-div {
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 3rem;
  padding-bottom: 4rem;
}

#print-button-div>button {
  padding: 10px 20px;
}

.bottom-stuff {
  margin-top: 2rem;
  border: 2px solid #F5F5F5;
  border-radius: 20px;
  padding: 30px;
}


#hidden-source {
  visibility: hidden;
  height: 0px;
}

/* @media query for smaller screens */
@media screen and (max-width: 1024px) {
  main {
    width: 80%;
  }
}

@media (max-width: 768px) {
  main {
    width: 90%;
  }

  body {
    font-size: 85%;
  }
}

@media screen and (max-width: 425px) {
  main {
    width: 95%;
    padding-top: 1rem;
  }

  html {
    font-size: 95%;
  }

  #input-div {
    padding-bottom: 1.5rem;
  }

  button,
  input[type="number"] {
    font-size: 12px;
  }

  .recipe-step input[type="checkbox"],
  .recipe-ingredient input[type="checkbox"] {
    margin-right: 10px;
  }

  input[type="text"] {
    width: 65%;
  }
}

@media screen and (max-width: 320px) {
  main {
    width: 97%;
    padding-top: 0.5rem;
  }

  html {
    font-size: 92%;
  }

  #input-div {
    padding-bottom: 1rem;
  }

  button,
  input[type="number"] {
    font-size: 12px;
  }

  .recipe-step input[type="checkbox"],
  .recipe-ingredient input[type="checkbox"] {
    margin-right: 10px;
  }

  input[type="text"] {
    width: 65%;
  }
}

@media print {

  body,
  #update-servings-div>button,
  #update-servings-div>label,
  #convert-button,
  #servings-button,
  #print-button-div {
    visibility: hidden;
  }

  #main-content {
    visibility: visible;
    position: absolute;
    left: 0;
    top: 0;
    color: black;
  }

  #hidden-source {
    visibility: visible;
    color: darkgrey;
    height: 100%;
  }

  input[type="number"] {
    color: black;
  }
}
</style>


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
      token: null,
      apiUrl: process.env.VUE_APP_API_URL,
      loading: false,
    };
  },
  methods: {
    async submitRecipeUrl() {
      try {
        if (!this.isLoggedIn) {
          console.error('No token found');
          return;
        }

        // Set loading to true to show loading indicator and change button text
        this.loading = true;

        const response = await axios.post(`${this.apiUrl}/scrape-recipe-steps`, {
          recipe_url: this.recipeUrl
        }, {
          headers: {
            Authorization: this.token
          }
        });

        // Assign response to recipeResponse to display recipe details
        this.recipeResponse = response.data;
        this.unitType = this.recipeResponse.original_unit_type;
        this.servingSizeInput = parseInt(this.recipeResponse.servings);

      } catch (error) {
        console.error('Error submitting recipe URL:', error.response ? error.response.data : error.message);
        // Set error message in recipeResponse to display error
        this.recipeResponse = { error: 'Please enter a valid URL.' };
      } finally {
        // Set loading back to false to hide loading indicator and restore button text
        this.loading = false;
      }
    },
    async convertUnits() {
      try {
        if (!this.isLoggedIn) {
          console.error('No token found');
          return;
        }
        const temp_unit = this.unitType === 'metric' ? 'si' : 'metric';
        const response = await axios.post(`${this.apiUrl}/convert-recipe-units`, {
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
        const response = await axios.post(`${this.apiUrl}/calculate-serving-ingredients`, {
          serving_size: this.servingSizeInput
        }, {
          headers: {
            Authorization: `${this.token}`
          }
        });
        this.recipeResponse.ingredients = response.data;
        this.servingSize = this.servingSizeInput;
      } catch (error) {
        console.error('Error calculating ingredients:', error.response ? error.response.data : error.message);
      }
    },
    async printPage() {
      window.print();
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