const express = require('express');
const mqtt = require('mqtt');
const app = express();
const port = 3000;
const http = require('http');
const server = http.createServer(app);
const path = require('path');
const { Server } = require("socket.io");
const io = new Server(server);
const routes = require('./src/routes');
const sensorModel = require('./src/models/sensors.model');

// Set EJS as the templating engine
app.set('view engine', 'ejs');

// Specify the directory where EJS files are located
app.set('views', path.join(__dirname, 'public/')); // Replace 'templates' with your desired directory


let sensorBuffer = [];

// Middleware to parse JSON data
app.use(express.json());

// Routes
app.use('/api', routes);

// MQTT setup
const mqttClient = mqtt.connect('mqtt://192.168.154.37:1883'); // Use your MQTT broker address
mqttClient.on('connect', () => {
    console.log('Connected to MQTT broker');

	// Subscribe to the temperature topic
    mqttClient.subscribe('home/sensors/data', (err) => {
        if(err){
            console.error("failed to suscribe to topic: ", err);
        }
    });
	// Subscribe to the another topic

});


mqttClient.on('message', async (topic, message) => {
    if (topic === 'home/sensors/data') {

        const get_payload_str = message.toString();
        console.log(`${topic} : payload string received : ${get_payload_str}\n`);
    
        const sensorData = convert_payload_str_to_obj(get_payload_str);

        console.log('payload: ', sensorData);

        // update web/client with data using socketIO
        io.emit('sensorData', sensorData);  

        //save sensor data(average) in database
        save_avg_sensor_data(sensorData);
    }

    // listen to other suscribe topics
    // if (topic == x){}
});


// Endpoint to network
app.get('/', (req, res) => {
    console.log("hello, world");
    res.status(200).send('Data received');
});

// // serve static files

//   // endpoint for showing graphs
//   app.get('/graph', (req, res) => {
//     console.log('connect get');
//     res.sendFile(__dirname + '/public/graph.html');
//   });

app.get('/detail', async (req, res) => {
    try {
        const data = await sensorModel.getAllSensorData();
        res.render('detail', { data }); // Assuming you're using a template engine
    } catch (error) {
        res.status(500).send('Error retrieving data');
    }
});

 

io.on('connection', (socket) => {
    console.log('A user connected to Socket.IO');

    // Handle checkbox data sent from the client
    socket.on('checkBoxData', (checkBoxData) => {
        console.log(`Live feedback from checkbox to MQTT: ${checkBoxData}`);

         // Send the retrieved data back to the client
         socket.emit('x', "mercy me");
        
        // Publish the checkbox data to the MQTT topic
        mqttClient.publish('esp/cmd', checkBoxData);
    });

    // Handle SensorDataWithinRange requests from the client
    socket.on('searchTimeRange', async (searchTime) => {
       
            // Query the database for sensor data within the specified time range
            const returnData = await sensorModel.getSensorDataWithinRange(searchTime);
            
            // Send the retrieved data back to the client
            socket.emit('recRange', returnData);
       
    });



});


function convert_payload_str_to_obj(payload_str){
    const values = payload_str.split(',');

    return {
        current: parseFloat(values[0]),
        voltage: parseFloat(values[1]),
    };
}

async function save_avg_sensor_data(data){
    sensorBuffer.push(data);

    // if 5 minutes (60 samples if collected every 5 seconds) have passed
    // calculate the averages and save to DB
    if (sensorBuffer.length >= 5){
        const avgCurrent = sensorBuffer.reduce((sum, d) => sum + d.current, 0) / sensorBuffer.length;
        const avgVoltage = sensorBuffer.reduce((sum, d) => sum + d.voltage, 0) / sensorBuffer.length;

        const dataObj = {
            current: parseFloat(avgCurrent).toFixed(2),
            voltage: parseFloat(avgVoltage).toFixed(2),
        };

        // database query to insert sensor data(average)
        const returnData = await sensorModel.createSensorData(dataObj);
        console.log("sensorModel.createSensorData: ", returnData);

        // clear the buffer for the next interval
        console.log("sensorBuffer: ", sensorBuffer);
        sensorBuffer = [];
    }
}


server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});