const pool = require('./db');

const createSensorDataTable = async () => {
    const query = `
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            current NUMERIC,
            voltage NUMERIC
        );
    `;
    
    try {
        await pool.query(query); // Execute the query
        console.log('Table "sensor_data" created or already exists.');
    } catch (err) {
        console.error('Error creating table:', err.message);
    }
};
createSensorDataTable();

const getAllSensorData = async () => {
    try {
      const result = await pool.query('SELECT * FROM sensor_data');
      return result.rows;
    } catch (err) {
      throw new Error(err);
    }
  };

  const getSensorDataById = async (id) => {
    try {
      const result = await pool.query('SELECT * FROM sensor_data WHERE id = $1', [id]);
      return result.rows[0];
    } catch (err) {
      throw new Error(err);
    }
  };

  const getSensorDataWithinRange = async (time) => {
    try {
        const querySpecificTimeRange = `
            SELECT *
            FROM sensor_data
            WHERE timestamp BETWEEN NOW() - INTERVAL '${time.timeEnd} hours' AND NOW() - INTERVAL '${time.timeStart} hours';
        `;
        const result = await pool.query(querySpecificTimeRange);
        return result.rows;
    
    } catch (err) {
      throw new Error(err);
    }
  };

  
    const createSensorData = async (data) => {
      const query = `
          INSERT INTO sensor_data (current, voltage)
          VALUES ($1, $2) RETURNING *;`;
      const values = [data.current, data.voltage];
  
      try {
          const result = await pool.query(query, values);
          return result.rows[0];
      } catch (err) {
          throw new Error(err)
      }
  };
  
  const deleteSensorData = async (id) => {
    try {
      const query = 'DELETE FROM sensor_data WHERE id = $1 RETURNING *;';
      const result = await pool.query(query, [id]);
      return result.rows[0];
    } catch (err) {
        console.error('Error executing query', err.stack);
        throw new Error(err.message);
    }
  };


module.exports = {
    getAllSensorData,
    getSensorDataById,
    getSensorDataWithinRange,
    createSensorData,
    deleteSensorData
};


