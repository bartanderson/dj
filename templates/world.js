// Initialize world state
let worldState = {
    currentLocation: null,
    party: [],
    activeQuests: [],
    discoveredLocations: []
};

// Load world data from server
async function loadWorldData() {
    const response = await fetch('/api/world-state');
    const data = await response.json();
    renderWorldMap(data.worldMap);
    worldState.currentLocation = data.currentLocation;
    renderLocationDetails(data.currentLocation);
    renderParty(data.party);
    renderQuests(data.activeQuests);
}

// Render world map
function renderWorldMap(mapData) {
    const worldMap = document.getElementById('world-map');
    worldMap.innerHTML = '';
    
    // Create interactive map using SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('viewBox', `0 0 ${mapData.width} ${mapData.height}`);
    
    // Draw terrain
    mapData.terrain.forEach(area => {
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', area.points);
        polygon.setAttribute('fill', area.fill);
        polygon.setAttribute('stroke', '#3a5f85');
        polygon.setAttribute('stroke-width', '1');
        svg.appendChild(polygon);
    });
    
    // Draw locations
    mapData.locations.forEach(location => {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', location.x);
        circle.setAttribute('cy', location.y);
        circle.setAttribute('r', '15');
        circle.setAttribute('fill', location.isCurrent ? '#4ecca3' : '#3a5f85');
        circle.setAttribute('data-location-id', location.id);
        circle.classList.add('location-marker');
        
        // Add hover effect
        circle.addEventListener('mouseenter', () => {
            document.getElementById('location-preview').textContent = location.name;
        });
        
        // Add click handler
        circle.addEventListener('click', () => {
            travelToLocation(location.id);
        });
        
        svg.appendChild(circle);
    });
    
    worldMap.appendChild(svg);
}

// Render location details
function renderLocationDetails(location) {
    const locationImage = document.getElementById('location-image');
    const description = document.getElementById('location-description');
    
    locationImage.style.backgroundImage = `url('${location.imageUrl}')`;
    description.innerHTML = `
        <h2>${location.name}</h2>
        <p>${location.description}</p>
        <div class="location-features">
            <h4>Features:</h4>
            <ul>
                ${location.features.map(f => `<li>${f}</li>`).join('')}
            </ul>
        </div>
        <div class="location-services">
            <h4>Services:</h4>
            <ul>
                ${location.services.map(s => `<li>${s}</li>`).join('')}
            </ul>
        </div>
    `;
}

// Travel to a new location
async function travelToLocation(locationId) {
    const response = await fetch(`/api/travel/${locationId}`, { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
        worldState.currentLocation = data.location;
        renderLocationDetails(data.location);
        renderWorldMap(data.worldMap);
    }
}

// Initialize on load
window.addEventListener('load', () => {
    loadWorldData();
    
    // Set up event listeners
    document.getElementById('enter-dungeon').addEventListener('click', enterDungeon);
    document.getElementById('create-character').addEventListener('click', createCharacter);
    document.getElementById('manage-inventory').addEventListener('click', openInventory);
    document.getElementById('talk-to-npcs').addEventListener('click', talkToNPCs);
});

// Enter dungeon from current location
function enterDungeon() {
    // Generate dungeon based on current location
    fetch('/api/generate-dungeon', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Switch to dungeon view
                window.location.href = '/dungeon';
            }
        });
}
