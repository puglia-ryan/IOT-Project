document.addEventListener('DOMContentLoaded', function() {
  const resultsDiv = document.getElementById('rankings');
  let roomsData = []; // Store fetched room data for sorting

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

  // Fetch all rooms initially
  fetchAllRooms();
});
