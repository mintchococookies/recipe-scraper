<template>
  <div id="app">
    <!-- Add meta title that will be used for print filename -->
    <meta :title="recipeResponse ? recipeResponse.recipe_name : 'Recipe'">
    <LoginComponent />
    <main>
      <h1>&#129386; Recipe Scraper</h1>
      <div id="input-div">
        <input type="text" v-model="recipeUrl" placeholder="Paste recipe URL" />
        <button id="submit-button" :disabled="loading" @click="submitRecipeUrl">{{ loading ? 'Loading..' : 'Search' }}</button>
      </div>
      
      <!-- Add loading overlay -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-content">
          <div class="loading-spinner"></div>
          <p class="loading-text">{{ currentLoadingText }}</p>
          <button class="cancel-button" @click="cancelOperation">Cancel</button>
        </div>
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
                  'metric' ? 'Convert to SI' : 'Convert to Metric (US)' }}</button>
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
          <p id="hidden-credits">✨ Recipe extracted with https://recipescraper.mintchococookies.com ✨</p>
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
          <p>We've done our best to train our recipe detectives to handle all sorts of website layouts, but
            occasionally they might encounter one that throws them a curveball.</p>
          <p>If you ever find a recipe that doesn't seem quite right, don't be shy! You could drop us a quick message at
            <a href="https://mintchococookies.com/">mintchococookies.com</a> and we'll be happy to put on our detective
            hats and see if we can fix it. Or we'll just check our logs hehe. 🕵🏻‍♀️
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
      <p>© Lilian 2025 | Created with Flask, BeautifulSoup & Vue JS </p>
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
  font-size: 0.7rem;
  bottom: 0;
  margin: 0 auto;
  text-align: center;
}

body {
  font-family: 'JetBrains Mono', monospace;
  background-color: #0A1828;
  color: #fff;
  font-size: 14px;
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
  font-size: 1.5rem;
}

h2 {
  font-size: 1.2rem;
}

h3 {
  font-size: 1rem;
}

.recipe-name {
  border-bottom: 1px solid rgba(245, 245, 245, 0.1);
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

.recipe-step {
  display: flex;
  align-items: flex-start;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s ease;
  position: relative;
}

.recipe-ingredient {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 8px;
  transition: background-color 0.3s ease;
  position: relative;
}

.recipe-step:hover,
.recipe-ingredient:hover {
  background-color: rgba(245, 245, 245, 0.1);
}

.recipe-step input[type="checkbox"],
.recipe-ingredient input[type="checkbox"] {
  margin-right: 20px;
  width: 18px;
  height: 18px;
  position: relative;
  z-index: 1;
}

.recipe-step-number {
  margin-right: 10px;
  position: relative;
  z-index: 1;
}

.recipe-step label,
.recipe-ingredient label {
  flex: 1;
  position: relative;
  z-index: 1;
}

#input-div {
  display: flex;
  justify-content: space-between;
  padding-bottom: 1.5rem;
  padding-top: 1.5rem;
  height: 4vh;
}

input[type="text"] {
  width: 70%;
  height: 100%;
  padding: 0 15px;
  font-size: 14px;
  border: 1px solid #F5F5F5;
  border-radius: 5px;
  outline: none;
  font-family: 'JetBrains Mono', monospace;
  background: #F5F5F5;
}

input[type="number"] {
  padding: 4px 0px 4px 10px;
  font-size: 14px;
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
  font-size: 14px;
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
  font-size: 80%;
  margin-bottom: 2rem;
}

.disclaimer h2 {
  font-size: 0.9rem;
  margin-bottom: 1.2rem;
  color: #F5F5F5;
}

.disclaimer p {
  line-height: 1.5;
  margin-bottom: 1rem;
  opacity: 0.9;
}

.limitations {
  padding-top: 1.5rem;
  font-size: 80%;
  border-top: 1px solid rgba(245, 245, 245, 0.1);
}

.limitations h3 {
  font-size: 0.9rem;
  color: #F5F5F5;
  margin-bottom: 1rem;
}

.limitations ul {
  list-style-type: none;
  padding-left: 0;
}

.limitations li {
  line-height: 1.5;
  margin-bottom: 0.8rem;
  opacity: 0.9;
}

a {
  color: #afeeee;
  font-weight: 600;
}

.recipe-name>h2 {
  font-weight: 1000;
}

#main-content {
  margin-top: 1rem;
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
  background: rgba(245, 245, 245, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(245, 245, 245, 0.1);
}

#hidden-source, #hidden-credits {
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
  @page {
    /* This will suggest the filename when saving the PDF */
    size: auto;
    margin: 20mm;
  }
  
  /* Rest of print styles */
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

  #hidden-source, #hidden-credits {
    visibility: visible;
    color: darkgrey;
    height: 100%;
  }

  #hidden-credits {
    font-size: 0.5rem;
    text-align: center;
    margin-top: 2rem;
  }

  input[type="number"] {
    color: black;
  }
}

/* Add loading overlay styles */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(10, 24, 40, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
  color: #fff;
}

.loading-spinner {
  width: 45px;
  height: 45px;
  border: 5px solid rgba(255, 255, 255, 0.2);
  border-top: 5px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 1rem;
  font-family: 'JetBrains Mono', monospace;
  color: #fff;
  margin-top: 20px;
  animation: fadeInOut 5s ease-in-out infinite;
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.cancel-button {
  margin-top: 20px;
  padding: 8px 20px;
  background-color: #F5F5F5;
  color: #0A1828;
  border: 2px solid #F5F5F5;
  font-weight: 600;
  transition: all 0.3s ease;
}

.cancel-button:hover {
  background-color: #0A1828;
  color: #F5F5F5;
}
</style>


<script>
import axios from 'axios';
import LoginComponent from './components/LoginComponent.vue';

// Create axios instance
const axiosInstance = axios.create();

// Add response interceptor
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If the error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to login again
        const loginResponse = await axios.post(`${process.env.VUE_APP_API_URL}/login`, {
          username: process.env.VUE_APP_USERNAME,
          password: process.env.VUE_APP_PASSWORD
        }, {
          withCredentials: true
        });
        
        const newToken = loginResponse.data.token;
        localStorage.setItem('jwt_token', newToken);
        
        // Update the token in the original request
        originalRequest.headers.Authorization = newToken;
        
        // Retry the original request with the new token
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // If refresh fails, clear the token and trigger re-login
        localStorage.removeItem('jwt_token');
        window.location.reload(); // This will trigger the login component to try logging in again
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

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
      loadingTexts: [
        "🧙‍♀️ Casting cooking spells...",
        "🥄 Stirring up some magic...",
        "📝 Taking notes from grandma's recipe book...",
        "🌿 Picking fresh herbs from the garden...",
        "🥘 Warming up the kitchen...",
        "👨‍🍳 Consulting with master chefs...",
        "📚 Reading ancient cooking scrolls...",
        "✨ Adding a pinch of magic..."
      ],
      currentLoadingText: "",
      loadingTextIndex: 0,
      cancelToken: null,
    };
  },
  methods: {
    shuffleArray(array) {
      const shuffled = [...array];
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
      }
      return shuffled;
    },

    startLoadingAnimation() {
      // Shuffle the loading texts array
      const shuffledTexts = this.shuffleArray(this.loadingTexts);
      this.currentLoadingText = shuffledTexts[0];
      this.loadingTextIndex = 0;
      
      // Change text every 850ms using the shuffled array
      this.loadingInterval = setInterval(() => {
        this.loadingTextIndex = (this.loadingTextIndex + 1) % shuffledTexts.length;
        this.currentLoadingText = shuffledTexts[this.loadingTextIndex];
      }, 850);
    },
    
    stopLoadingAnimation() {
      if (this.loadingInterval) {
        clearInterval(this.loadingInterval);
      }
    },
    
    async submitRecipeUrl() {
      if (!this.recipeUrl) return;
      
      this.loading = true;
      this.startLoadingAnimation();
      
      // Create a new cancel token for this request
      this.cancelToken = axios.CancelToken.source();
      
      try {
        if (!this.isLoggedIn) {
          console.error('No token found');
          return;
        }

        this.recipeResponse = null; // Clear previous response

        const response = await axiosInstance.post(`${this.apiUrl}/scrape-recipe-steps`, {
          recipe_url: this.recipeUrl
        }, {
          headers: {
            Authorization: this.token
          },
          withCredentials: true,
          cancelToken: this.cancelToken.token
        });

        this.recipeResponse = response.data;
        this.unitType = this.recipeResponse.original_unit_type;
        this.servingSizeInput = parseInt(this.recipeResponse.servings);

      } catch (error) {
        if (axios.isCancel(error)) {
          console.log('Request cancelled:', error.message);
          this.recipeResponse = null;
        } else {
          console.error('Error submitting recipe URL:', error.response ? error.response.data : error.message);
          
          // More specific error handling
          if (error.response?.status === 401) {
            this.recipeResponse = { error: 'Your session has expired. Please refresh the page to continue.' };
          } else if (error.response?.status === 400) {
            this.recipeResponse = { error: 'Please enter a valid recipe URL.' };
          } else if (error.response?.status === 500) {
            this.recipeResponse = { error: 'Sorry, we encountered an error while processing this recipe. Please try again later.' };
          } else {
            this.recipeResponse = { error: 'An unexpected error occurred. Please try again.' };
          }
        }
      } finally {
        this.loading = false;
        this.stopLoadingAnimation();
        this.cancelToken = null;
      }
    },
    async convertUnits() {
      try {
        if (!this.isLoggedIn) {
          console.error('No token found');
          return;
        }
        const temp_unit = this.unitType === 'metric' ? 'si' : 'metric';
        const response = await axiosInstance.post(`${this.apiUrl}/convert-recipe-units`, {
          unit_type: temp_unit,
          ingredients: this.recipeResponse.ingredients
        }, {
          headers: {
            Authorization: `${this.token}`
          },
          withCredentials: true
        });
        this.recipeResponse.ingredients = response.data;
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
        const response = await axiosInstance.post(`${this.apiUrl}/calculate-serving-ingredients`, {
          serving_size: this.servingSizeInput
        }, {
          headers: {
            Authorization: `${this.token}`
          },
          withCredentials: true
        });
        this.recipeResponse.ingredients = response.data;
        this.servingSize = this.servingSizeInput;
      } catch (error) {
        console.error('Error calculating ingredients:', error.response ? error.response.data : error.message);
      }
    },
    async printPage() {
      // Set the document title to the recipe name before printing
      if (this.recipeResponse && this.recipeResponse.recipe_name) {
        const originalTitle = document.title;
        const recipeNameLower = this.recipeResponse.recipe_name.toLowerCase();
        const recipeLower = 'recipe';
        document.title = recipeNameLower.endsWith(recipeLower) 
          ? this.recipeResponse.recipe_name 
          : `${this.recipeResponse.recipe_name} Recipe`;
        
        // Print and restore original title
        window.print();
        document.title = originalTitle;
      } else {
        window.print();
      }
    },
    cancelOperation() {
      if (this.cancelToken) {
        this.cancelToken.cancel('Operation cancelled by user');
      }
      this.loading = false;
      this.stopLoadingAnimation();
    },
  },
  mounted() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      this.token = token;
      this.isLoggedIn = true;
    } else {
      // If no token, trigger login component to try logging in
      this.isLoggedIn = false;
    }
  },
  beforeUnmount() {
    this.stopLoadingAnimation();
  }
};
</script>