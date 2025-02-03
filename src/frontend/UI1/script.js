const form = document.getElementById('preferences-form');
const temperatureSlider = document.getElementById('temperature-slider');
const temperatureValue = document.getElementById('temperature-value');
const noiseSlider = document.getElementById('noise-slider');
const noiseValue = document.getElementById('noise-value');

// Update displayed values dynamically
temperatureSlider.addEventListener('input', () => {
  temperatureValue.textContent = temperatureSlider.value;
});

noiseSlider.addEventListener('input', () => {
  noiseValue.textContent = noiseSlider.value;
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  
  const resultsDiv = document.getElementById('rankings');
  const timeSlot = document.getElementById('time-slot').value.trim();
  const temperatureImportanceSelect = document.getElementById('temperature-importance');
  const noiseImportanceSelect = document.getElementById('noise-importance');

  const temperature = temperatureSlider.value;
  const noise = noiseSlider.value;
  const temperatureImportance = temperatureImportanceSelect.value;
  const noiseImportance = noiseImportanceSelect.value;

  // Validate time slot format
  if (!timeSlot.match(/^\d{2}:\d{2}-\d{2}:\d{2}$/)) {
    resultsDiv.innerHTML = "<p style='color: red;'>Invalid time format. Use HH:MM-HH:MM</p>";
    return;
  }

  try {
    const response = await fetch('http://127.0.0.1:5009/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        temperature, 
        noise, 
        time_slot: timeSlot,
        temperature_importance: temperatureImportance,
        noise_importance: noiseImportance
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Error:', errorData);
      resultsDiv.innerHTML = `<p style='color: red;'>Error: ${errorData.error}</p>`;
      return;
    }

    const data = await response.json();

    // Display results
    if (data.rooms && data.rooms.length > 0) {
      resultsDiv.innerHTML = `
        <table border="1" style="width: 100%; border-collapse: collapse;">
          <thead>
            <tr>
              <th style="padding: 8px; text-align: left;">Rank</th>
              <th style="padding: 8px; text-align: left;">Room</th>
              <th style="padding: 8px; text-align: left;">Facilities</th>
            </tr>
          </thead>
          <tbody>
            ${data.rooms.map(room => `
              <tr>
                <td style="padding: 8px;">${room.rank}</td>
                <td style="padding: 8px;">${room.room_name}</td>
                <td style="padding: 8px;">
                  ${room.facilities ? Object.entries(room.facilities)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join('<br>') : "No facilities available"}
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    } else {
      resultsDiv.innerHTML = "<p>No rooms match the criteria.</p>";
    }

  } catch (error) {
    console.error("Error fetching recommendations:", error);
    resultsDiv.innerHTML = "<p style='color: red;'>Unexpected error occurred. Please try again.</p>";
  }
});
