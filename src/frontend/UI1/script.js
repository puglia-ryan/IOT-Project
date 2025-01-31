document.addEventListener('DOMContentLoaded', function () {
  const temperatureSlider = document.getElementById('temperature-slider');
  const temperatureValue = document.getElementById('temperature-value');
  const form = document.getElementById('preferences-form');
  const resultsDiv = document.getElementById('rankings');

  temperatureSlider.addEventListener('input', function () {
    temperatureValue.textContent = `${temperatureSlider.value}°C`;
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // Clear previous results
    resultsDiv.innerHTML = '';

    const temperature = temperatureSlider.value;
    const timeSlot = document.getElementById('time-slot').value.trim();

    if (!timeSlot.match(/^\d{2}:\d{2}-\d{2}:\d{2}$/)) {
      resultsDiv.innerHTML = "<p style='color: red;'>Invalid time format. Use HH:MM-HH:MM</p>";
      return;
    }
    try {
      const response = await fetch('http://127.0.0.1:5009/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temperature, time_slot: timeSlot })
      });
    
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error:', errorData);  // Log to console for debugging
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
});
