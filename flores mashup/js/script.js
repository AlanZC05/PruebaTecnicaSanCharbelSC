document.addEventListener('DOMContentLoaded', () => {
  
    const UI = {
        searchBtn: document.getElementById('search-btn'),
        searchInput: document.getElementById('flower-search'),
        loading: document.getElementById('loading'),
        results: document.getElementById('results'),
        error: document.getElementById('error'),
        resultTitle: document.getElementById('result-title'),
        imageGallery: document.getElementById('image-gallery'),
        generalInfo: document.getElementById('general-info'),
        botanicalInfo: document.getElementById('botanical-info'),
        careInfo: document.getElementById('care-info'),
        apiBadges: document.querySelector('.api-badges')
    };

    
    UI.searchBtn.addEventListener('click', searchFlower);
    UI.searchInput.addEventListener('keypress', (e) => e.key === 'Enter' && searchFlower());

   
    const state = {
        currentSearch: '',
        lastResults: null,
        activeAPIs: {
            plant: true,
            trefle: true,
            perenual: true
        }
    };

   
    async function searchFlower() {
        const query = UI.searchInput.value.trim();
        
        if (!query || query.length < 3) {
            showError('Ingresa al menos 3 caracteres');
            return;
        }

        resetUI();
        state.currentSearch = query;
        UI.loading.classList.remove('hidden');

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `query=${encodeURIComponent(query)}`
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            if (data.error) throw new Error(data.error);
            if (!data.plant_api && !data.trefle && !data.perenual) {
                throw new Error('No se encontraron resultados');
            }

            state.lastResults = data;
            displayResults(data);
            
        } catch (error) {
            console.error('Search error:', error);
            showError(error.message || 'Error en la búsqueda');
        } finally {
            UI.loading.classList.add('hidden');
        }
    }

   
    function displayResults(data) {
       
        const displayName = data.plant_api?.common_name || 
                          data.trefle?.common_name || 
                          data.perenual?.common_name || 
                          data.query;
        
        UI.resultTitle.textContent = displayName;
        UI.resultTitle.innerHTML += data.stats ? 
            `<small> (${data.stats.apis_responded} APIs respondieron en ${data.stats.processing_time})</small>` : '';

        
        renderImages(data);
        
       
        renderInfoSection(UI.generalInfo, [
            { label: 'Nombre científico', value: data.plant_api?.scientific_name },
            { label: 'Familia', value: data.plant_api?.family },
            { label: 'Descripción', value: data.plant_api?.description }
        ]);

        renderInfoSection(UI.botanicalInfo, [
            { label: 'Nombre científico (Trefle)', value: data.trefle?.scientific_name },
            { label: 'Familia (Trefle)', value: data.trefle?.family }
        ]);

        renderInfoSection(UI.careInfo, [
            { label: 'Riego', value: data.perenual?.watering },
            { label: 'Luz solar', value: Array.isArray(data.perenual?.sunlight) ? 
                data.perenual.sunlight.join(', ') : data.perenual?.sunlight },
            { label: 'Nivel de cuidado', value: data.perenual?.care_level }
        ]);

       
        updateAPIBadges(data);
        
        UI.results.classList.remove('hidden');
    }

    
    function renderImages(data) {
        UI.imageGallery.innerHTML = '';
        
        const images = [
            { src: data.plant_api?.image_url, alt: 'Plant API', api: 'plant' },
            { src: data.trefle?.image_url, alt: 'Trefle API', api: 'trefle' },
            { src: data.perenual?.image_url, alt: 'Perenual API', api: 'perenual' }
        ].filter(img => img.src);

        if (images.length === 0) {
            UI.imageGallery.innerHTML = '<p class="no-images">No se encontraron imágenes</p>';
            return;
        }

        images.forEach(img => {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'img-container';
            
            const imgElement = document.createElement('img');
            imgElement.src = img.src;
            imgElement.alt = img.alt;
            imgElement.onerror = () => imgContainer.remove();
            
            const imgCaption = document.createElement('span');
            imgCaption.className = 'img-caption';
            imgCaption.textContent = img.alt;
            
            imgContainer.append(imgElement, imgCaption);
            UI.imageGallery.appendChild(imgContainer);
        });
    }

    function renderInfoSection(container, items) {
        const validItems = items.filter(item => item.value);
        
        if (validItems.length === 0) {
            container.innerHTML = '<p>No hay información disponible</p>';
            return;
        }
        
        container.innerHTML = '<ul>' + 
            validItems.map(item => 
                `<li><strong>${item.label}:</strong> ${item.value}</li>`
            ).join('') + 
            '</ul>';
    }

    function updateAPIBadges(data) {
        const apis = {
            plant: !!data.plant_api,
            trefle: !!data.trefle,
            perenual: !!data.perenual
        };
        
        UI.apiBadges.innerHTML = Object.entries(apis)
            .map(([api, active]) => 
                `<span class="api-badge ${active ? 'active' : 'inactive'}">${api}</span>`
            ).join('');
    }

    function resetUI() {
        UI.loading.classList.add('hidden');
        UI.results.classList.add('hidden');
        UI.error.classList.add('hidden');
    }

    function showError(message) {
        UI.error.textContent = message;
        UI.error.classList.remove('hidden');
    }

async function searchFlower() {
    const query = document.getElementById('flower-search').value.trim();
    const loadingElement = document.getElementById('loading');
    const resultsElement = document.getElementById('results');
    const errorElement = document.getElementById('error');
    
    
    const nonFlowerTerms = ['auto', 'casa', 'perro', 'gato', 'computadora', 'libro', 'telefono'];
    
    
    if (query.length === 0) {
      showError('⚠️ Por favor ingresa el nombre de una flor', popularFlowers.slice(0, 6));
      return;
    }
    
    
    if (nonFlowerTerms.some(term => term.toLowerCase() === query.toLowerCase())) {
      showError(`"${query}" no parece ser una flor. Intenta con:`, popularFlowers);
      return;
    }
    
    
    resetUI();
    loadingElement.style.display = 'block';
    
    try {
      
    } catch (error) {
      showError(error.message, error.suggestions || []);
    } finally {
      loadingElement.style.display = 'none';
    }
  }
  function showError(message, suggestions = []) {
    const errorElement = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');
    const suggestionsElement = document.getElementById('error-suggestions');
    
    errorMessage.innerHTML = message;
    
    if (suggestions.length > 0) {
      suggestionsElement.innerHTML = `
        <div class="mt-3">
          <p class="mb-2">Quizás quisiste decir:</p>
          <div class="d-flex flex-wrap justify-content-center gap-2">
            ${suggestions.map(flower => `
              <span class="suggestion-chip" 
                    onclick="document.getElementById('flower-search').value='${flower}';searchFlower()">
                ${flower}
              </span>
            `).join('')}
          </div>
        </div>`;
    } else {
      suggestionsElement.innerHTML = '';
    }
    
    errorElement.style.display = 'block';
    
   
    errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

const validFlowers = [
    'rosa', 'tulipán', 'girasol', 'orquídea', 'alcatraz', 'cala', 
    'lirio', 'margarita', 'hortensia', 'jazmín', 'lavanda', 'peonía'
  ];
  

  function isValidFlower(query) {
    return validFlowers.some(flower => 
      flower.toLowerCase() === query.toLowerCase() ||
      query.toLowerCase().includes(flower.toLowerCase())
    );
  }
  

  if (!isValidFlower(query)) {
    const similarFlowers = validFlowers.filter(flower => 
      flower.toLowerCase().includes(query.toLowerCase().substring(0, 3))
    );
    
    showError(`"${query}" no es reconocido como una flor válida.`, 
              similarFlowers.length > 0 ? similarFlowers : popularFlowers);
    return;
  }
   
    const urlParams = new URLSearchParams(window.location.search);
    const initialQuery = urlParams.get('q');
    if (initialQuery) {
        UI.searchInput.value = initialQuery;
        searchFlower();
    }
});