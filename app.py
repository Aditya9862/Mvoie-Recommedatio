import pickle
import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# =========================
# TMDB API Setup
# =========================
API_KEY = "8265bd1679663a7ea12ac168da84d2e8"  # replace with your TMDB key

# Setup requests session with retry logic
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)


# Get TMDB image base URL dynamically
@st.cache_data
def get_base_url():
    try:
        url = f"https://api.themoviedb.org/3/configuration?api_key={API_KEY}"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['images']['secure_base_url'] + "w500"
    except Exception as e:
        st.error(f"⚠️ Error fetching TMDB configuration: {e}")
        # fallback hardcoded URL
        return "https://image.tmdb.org/t/p/w500"


BASE_URL = get_base_url()


# Fetch poster for a given movie ID
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return BASE_URL + poster_path
        else:
            return "https://via.placeholder.com/500x750?text=No+Poster"
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Could not fetch poster for movie ID {movie_id}. Using placeholder.")
        return "https://via.placeholder.com/500x750?text=Error"


# Recommend movies
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)
    return recommended_movie_names, recommended_movie_posters


# =========================
# Streamlit UI
# =========================
st.header('🎬 Movie Recommender System')

# Load data
movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    recommended_movie_names, recommended_movie_posters = recommend(selected_movie)
    cols = st.columns(5)
    for i, col in enumerate(cols):
        with col:
            st.text(recommended_movie_names[i])
            st.image(recommended_movie_posters[i])
