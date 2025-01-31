const apiUrl = "http://localhost:5009/rooms_with_metrics";

let tempChart, co2Chart, humidityChart, soundChart;

// Fetch unique rooms and populate dropdown
async function fetchRooms() {
    try {
        let response = await fetch(apiUrl);
        let data = await response.json();
        
        // Extract unique room names
        let rooms = [...new Set(data.rooms_with_metrics.map(room => room.room_name))];

        let select = document.getElementById("roomSelect");
        select.innerHTML = "";

        rooms.forEach(room => {
            let option = document.createElement("option");
            option.value = room;
            option.textContent = room;
            select.appendChild(option);
        });

        // Load data for first room
        fetchData();
    } catch (error) {
        console.error("Error fetching rooms:", error);
    }
}

// Fetch time-series data for selected room
async function fetchData() {
    let selectedRoom = document.getElementById("roomSelect").value;
    
    try {
        let response = await fetch(apiUrl);
        let data = await response.json();
        
        let roomData = data.rooms_with_metrics.filter(room => room.room_name === selectedRoom);

        if (roomData.length > 0) {
            updateCharts(roomData);
        } else {
            console.error("No data for selected room.");
        }
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

// Update time-series charts
function updateCharts(roomData) {
    // Extract timestamps and sensor values
    const timestamps = roomData.map(entry => new Date(entry.timestamp).toLocaleTimeString());
    const temperatures = roomData.map(entry => entry.temperature || 0);
    const co2Levels = roomData.map(entry => entry.co2_level || 0);
    const humidityLevels = roomData.map(entry => entry.humidity || 0);
    const soundLevels = roomData.map(entry => entry.sound_level || 0);

    const ctx1 = document.getElementById("tempChart").getContext("2d");
    const ctx2 = document.getElementById("co2Chart").getContext("2d");
    const ctx3 = document.getElementById("humidityChart").getContext("2d");
    const ctx4 = document.getElementById("soundChart").getContext("2d");

    // Destroy old charts if they exist
    if (tempChart) tempChart.destroy();
    if (co2Chart) co2Chart.destroy();
    if (humidityChart) humidityChart.destroy();
    if (soundChart) soundChart.destroy();

    // Create new line charts with time-series data
    tempChart = new Chart(ctx1, createTimeChartConfig("Temperature (°C)", timestamps, temperatures, "rgba(255, 99, 132, 0.6)"));
    co2Chart = new Chart(ctx2, createTimeChartConfig("CO2 Level (ppm)", timestamps, co2Levels, "rgba(54, 162, 235, 0.6)"));
    humidityChart = new Chart(ctx3, createTimeChartConfig("Humidity (%)", timestamps, humidityLevels, "rgba(75, 192, 192, 0.6)"));
    soundChart = new Chart(ctx4, createTimeChartConfig("Sound Level (dB)", timestamps, soundLevels, "rgba(255, 206, 86, 0.6)"));
}

// Generate time-series chart config
function createTimeChartConfig(label, timestamps, values, color) {
    return {
        type: "line",
        data: {
            labels: timestamps,
            datasets: [{
                label: label,
                data: values,
                backgroundColor: color,
                borderColor: color,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Time"
                    }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    };
}

// Initialize the dashboard
fetchRooms();

