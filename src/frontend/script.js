document.addEventListener('DOMContentLoaded', function() {
  const resultsDiv = document.getElementById('rankings');
  const metricsDiv = document.getElementById('metrics');

  let roomsData = [];
  let envData = [];
  // Function to sort rooms by a given column
  function sortRooms(column, type = 'string') {
      let ascending = true;

      return function() {
          roomsData.sort((a, b) => {
              let valA = a[column] || "";
              let valB = b[column] || "";

              if (type === 'number') {
                  valA = parseInt(valA.match(/\d+/) || 0);  // Extract numeric part (e.g., Room 10 -> 10)
                  valB = parseInt(valB.match(/\d+/) || 0);
              } else if (type === 'time') {
                  valA = valA ? valA.split('-')[0] : "00:00"; // Use start time for sorting
                  valB = valB ? valB.split('-')[0] : "00:00";
              }

              return ascending ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
          });

          ascending = !ascending; // Toggle sorting order
          displayRooms(); // Refresh table after sorting
      };
  }

  // Function to display rooms in table
  function displayRooms() {
      resultsDiv.innerHTML = `
          <table border="1" style="width: 100%; border-collapse: collapse;">
              <thead>
                  <tr>
                      <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-room">Room ⬍</th>
                      <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-time">Time Slot ⬍</th>
                      <th style="padding: 8px; text-align: left;">Facilities</th>
                  </tr>
              </thead>
              <tbody>
                  ${roomsData.map(room => `
                      <tr>
                          <td style="padding: 8px;">${room.room_name}</td>
                          <td style="padding: 8px;">${room.time_slot || "Not Available"}</td>
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

      // Add sorting event listeners
      document.getElementById("sort-room").addEventListener("click", sortRooms("room_name", "number"));
      document.getElementById("sort-time").addEventListener("click", sortRooms("time_slot", "time"));
  }

  // Fetch and display all rooms when the page loads
  async function fetchAllRooms() {
      try {
          const response = await fetch('http://127.0.0.1:5009/rooms');

          if (!response.ok) {
              const errorData = await response.json();
              console.error('Error:', errorData);
              resultsDiv.innerHTML = `<p style='color: red;'>Error: ${errorData.error}</p>`;
              return;
          }

          const data = await response.json();
          roomsData = data.rooms || [];
          displayRooms(); // Show table after fetching data

      } catch (error) {
          console.error("Error fetching all rooms:", error);
          resultsDiv.innerHTML = "<p style='color: red;'>Unexpected error occurred. Please try again.</p>";
      }
  }
    // Function to display environmental metrics in table
    function displayMetrics() {
        metricsDiv.innerHTML = `
            <table border="1" style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">Room Name</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">Temperature</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">CO2 Level</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">Humidity</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">VOC Level</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">PM10</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">PM2.5</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;">Sound Level</th>
                    </tr>
                </thead>
                <tbody>
                    ${envData.map(env => `
                        <tr>
                            <td style="padding: 8px;">${env.room_name}</td>
                            <td style="padding: 8px;">${env.temperature_min} - ${env.temperature_max}</td>
                            <td style="padding: 8px;">${env.co2_level}</td>
                            <td style="padding: 8px;">${env.humidity}</td>
                            <td style="padding: 8px;">${env.voc_level}</td>
                            <td style="padding: 8px;">${env.PM10}</td>
                            <td style="padding: 8px;">${env.sound_level}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    }

    // Fetch and display environmental metrics
    async function fetchRoomMetrics() {
        try {
            const response = await fetch('http://127.0.0.1:5009/environmental-metrics');  // Adjust endpoint if necessary

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error:', errorData);
                metricsDiv.innerHTML = `<p style='color: red;'>Error: ${errorData.error}</p>`;
                return;
            }

            const data = await response.json();
            envData = data.metrics || [];
            displayMetrics(); // Show environmental metrics after fetching data

        } catch (error) {
            console.error("Error fetching environmental metrics:", error);
            metricsDiv.innerHTML = "<p style='color: red;'>Unexpected error occurred. Please try again.</p>";
        }
    }



  // Fetch all rooms initially
  fetchAllRooms();
  fetchRoomMetrics();
});
