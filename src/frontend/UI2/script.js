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
                    valA = parseFloat(valA) || 0;
                    valB = parseFloat(valB) || 0;
                } else if (type === 'time') {
                    valA = valA ? valA.split('-')[0] : "00:00"; // Sort by start time
                    valB = valB ? valB.split('-')[0] : "00:00";
                }

                return ascending ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
            });

            ascending = !ascending; // Toggle sorting order
            displayRooms(); // Refresh table after sorting
        };
    }

    // Function to display rooms in a table
    function displayRooms() {
        resultsDiv.innerHTML = `
            <table border="1" style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-room">Room ⬍</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-time">Time Slot ⬍</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-temp">Temp (°C) ⬍</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-co2">CO₂ (ppm) ⬍</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-humidity">Humidity (%) ⬍</th>
                        <th style="cursor:pointer; padding: 8px; text-align: left;" id="sort-sound">Sound (dB) ⬍</th>
                        <th style="padding: 8px; text-align: left;">Facilities</th>
                    </tr>
                </thead>
                <tbody>
                    ${roomsData.map(room => `
                        <tr>
                            <td style="padding: 8px;">${room.room_name}</td>
                            <td style="padding: 8px;">${room.time_slot || "Not Available"}</td>
                            <td style="padding: 8px;">${room.temperature || "N/A"}</td>
                            <td style="padding: 8px;">${room.co2_level || "N/A"}</td>
                            <td style="padding: 8px;">${room.humidity || "N/A"}</td>
                            <td style="padding: 8px;">${room.sound_level || "N/A"}</td>
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
        document.getElementById("sort-room").addEventListener("click", sortRooms("room_name", "string"));
        document.getElementById("sort-time").addEventListener("click", sortRooms("time_slot", "time"));
        document.getElementById("sort-temp").addEventListener("click", sortRooms("temperature", "number"));
        document.getElementById("sort-co2").addEventListener("click", sortRooms("co2_level", "number"));
        document.getElementById("sort-humidity").addEventListener("click", sortRooms("humidity", "number"));
        document.getElementById("sort-sound").addEventListener("click", sortRooms("sound_level", "number"));
    }

    // Fetch and display all rooms when the page loads
    async function fetchAllRooms() {
        try {
            const response = await fetch('http://127.0.0.1:5009/rooms_with_metrics');

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error:', errorData);
                resultsDiv.innerHTML = `<p style='color: red;'>Error: ${errorData.error}</p>`;
                return;
            }

            const data = await response.json();
            roomsData = data.rooms_with_metrics || [];
            displayRooms(); // Show table after fetching data

        } catch (error) {
            console.error("Error fetching room metrics:", error);
            resultsDiv.innerHTML = "<p style='color: red;'>Unexpected error occurred. Please try again.</p>";
        }
    }

    // Fetch all rooms initially
    fetchAllRooms();
});

