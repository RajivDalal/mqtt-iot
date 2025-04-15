import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import time
import logging
import random

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="Sensor Data Dashboard",
    page_icon="📊",
    layout="wide"
)

# Function to generate simulated sensor data
def generate_simulated_data(start_date, end_date, sensor_ids=None, interval_minutes=15):
    """
    Generate simulated sensor data for given date range and sensors.
    
    Args:
        start_date: Start datetime
        end_date: End datetime
        sensor_ids: List of sensor IDs (if None, creates data for 3 sensors)
        interval_minutes: Data interval in minutes
    
    Returns:
        List of data points
    """
    logger.info(f"Generating simulated data from {start_date} to {end_date}")
    
    # If no sensor IDs provided, create some
    if not sensor_ids:
        sensor_ids = ["sensor-001", "sensor-002", "sensor-003"]
    
    # Create time range
    current_time = start_date
    data_points = []
    
    # Base values for each sensor (for realistic, consistent values)
    base_values = {}
    for sensor_id in sensor_ids:
        base_values[sensor_id] = {
            "voltage_base": random.uniform(110, 125),
            "current_base": random.uniform(4, 8)
        }
    
    # Create data points at regular intervals
    while current_time <= end_date:
        for sensor_id in sensor_ids:
            # Get base values for this sensor
            voltage_base = base_values[sensor_id]["voltage_base"]
            current_base = base_values[sensor_id]["current_base"]
            
            # Add some random variation
            voltage = voltage_base + random.uniform(-5, 5)
            current = current_base + random.uniform(-1, 1)
            
            # Add time-based variation (voltage drops slightly in evenings)
            hour = current_time.hour
            if 18 <= hour <= 22:
                voltage *= 0.98  # 2% voltage drop in evening
            
            # Create data point
            data_point = {
                "id": sensor_id,
                "timestamp": current_time.isoformat(),
                "voltage": voltage,
                "current": current,
                "status": "normal" if random.random() > 0.05 else "warning"
            }
            
            data_points.append(data_point)
        
        # Move to next time interval
        current_time += timedelta(minutes=interval_minutes)
    
    logger.info(f"Generated {len(data_points)} simulated data points")
    return data_points

# Function to fetch simulated data (replaces API call)
def fetch_all_sensor_data():
    try:
        logger.info("Generating simulated sensor data for all sensors")
        
        # Generate for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        data = generate_simulated_data(start_date, end_date)
        logger.info(f"Generated {len(data)} records")
        return data
    except Exception as e:
        error_msg = f"Error generating data: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
        return []

def fetch_sensor_data_by_id(sensor_id):
    try:
        logger.info(f"Generating simulated data for sensor ID: {sensor_id}")
        
        # Generate for the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        data = generate_simulated_data(start_date, end_date, [sensor_id])
        logger.info(f"Generated {len(data)} records")
        return data
    except Exception as e:
        error_msg = f"Error generating data for sensor {sensor_id}: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
        return None

def fetch_sensor_data_in_range(start_date, end_date, sensor_id=None):
    try:
        logger.info(f"Generating data in range: {start_date} to {end_date}")
        
        if sensor_id and sensor_id != "All":
            data = generate_simulated_data(start_date, end_date, [sensor_id])
        else:
            data = generate_simulated_data(start_date, end_date)
        
        logger.info(f"Generated {len(data)} records in range")
        return data
    except Exception as e:
        error_msg = f"Error generating data in range: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
        return []

# Function to transform sensor data into pandas DataFrame
def process_sensor_data(data):
    try:
        logger.info("Processing sensor data")
        
        if not data:
            logger.warning("No data to process")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        logger.info(f"Created DataFrame with shape: {df.shape}")
        
        if df.empty:
            logger.warning("DataFrame is empty after creation")
            return df
            
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            try:
                logger.info("Converting timestamp column to datetime")
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                logger.info("Timestamp conversion successful")
            except Exception as e:
                logger.error(f"Error converting timestamps: {str(e)}")
        
        # Convert voltage and current to standard float
        if 'voltage' in df.columns:
            try:
                logger.info("Converting voltage to float")
                df['voltage'] = df['voltage'].astype(float)
            except Exception as e:
                logger.error(f"Error converting voltage: {str(e)}")
        
        if 'current' in df.columns:
            try:
                logger.info("Converting current to float")
                df['current'] = df['current'].astype(float)
            except Exception as e:
                logger.error(f"Error converting current: {str(e)}")
        
        # Calculate power (voltage * current)
        if 'voltage' in df.columns and 'current' in df.columns:
            try:
                logger.info("Calculating power from voltage and current")
                df['power'] = df['voltage'] * df['current']
                logger.info("Power calculation successful")
            except Exception as e:
                logger.error(f"Error calculating power: {str(e)}")
        
        # Ensure id is string type
        if 'id' in df.columns:
            try:
                logger.info("Converting id to string")
                df['id'] = df['id'].astype(str)
            except Exception as e:
                logger.error(f"Error converting id: {str(e)}")
        
        logger.info("Data processing complete")
        return df
        
    except Exception as e:
        error_msg = f"Error in process_sensor_data: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
        # Return empty DataFrame on error
        return pd.DataFrame()

# Function to simulate real-time data flow
def simulate_real_time_data(df, simulation_speed=1):
    """
    Simulates real-time data by taking data points from the DataFrame at specified intervals.
    Returns a generator that yields one data point at a time.
    
    Args:
        df: pandas DataFrame with sensor data
        simulation_speed: how many data points to advance per second (default: 1)
    """
    if df.empty or 'timestamp' not in df.columns:
        logger.warning("Cannot simulate real-time data with empty DataFrame or missing timestamp")
        return
    
    # Sort by timestamp to ensure proper sequence
    df = df.sort_values('timestamp')
    
    # Get current simulation position from session state
    if 'simulation_index' not in st.session_state:
        st.session_state['simulation_index'] = 0
    
    index = st.session_state['simulation_index']
    
    # Make sure index is within bounds
    if index >= len(df):
        index = 0
    
    # Get the next data point
    data_point = df.iloc[index:index+simulation_speed]
    
    # Update session state with new index
    st.session_state['simulation_index'] = (index + simulation_speed) % len(df)
    
    return data_point

# Function to update real-time data buffer
def update_real_time_buffer(new_data):
    """
    Updates the real-time data buffer with new data points.
    Maintains a fixed buffer size to avoid memory issues.
    
    Args:
        new_data: pandas DataFrame with new data points to add
    """
    if 'real_time_buffer' not in st.session_state:
        # Initialize buffer with new data
        st.session_state['real_time_buffer'] = new_data
        return
    
    # Max buffer size (number of data points to keep)
    MAX_BUFFER_SIZE = 100
    
    # Combine existing buffer with new data
    buffer = pd.concat([st.session_state['real_time_buffer'], new_data])
    
    # Keep only the most recent MAX_BUFFER_SIZE data points
    if len(buffer) > MAX_BUFFER_SIZE:
        buffer = buffer.iloc[-MAX_BUFFER_SIZE:]
    
    # Update session state
    st.session_state['real_time_buffer'] = buffer

# Dashboard title
st.title("Power Monitoring Dashboard")
st.markdown("### Real-time voltage and current monitoring with power analysis")

# Sidebar for controls
st.sidebar.header("Dashboard Controls")

# Auto-refresh option
auto_refresh = st.sidebar.checkbox("Auto-refresh data", value=False)
refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 
                                     min_value=5, max_value=60, value=30, 
                                     disabled=not auto_refresh)

# Real-time simulation mode
simulation_mode = st.sidebar.checkbox("Enable real-time simulation", value=False)
simulation_speed = st.sidebar.slider("Simulation speed (points/second)", 
                                    min_value=1, max_value=10, value=1, 
                                    disabled=not simulation_mode)

# Date range selector
st.sidebar.header("Date Range")
today = datetime.now()
default_start = today - timedelta(days=7)

start_date = st.sidebar.date_input("Start date", default_start)
end_date = st.sidebar.date_input("End date", today)

# Time range for the selected dates
start_time = st.sidebar.time_input("Start time", value=datetime.min.time())
end_time = st.sidebar.time_input("End time", value=datetime.max.time())

# Combine date and time
start_datetime = datetime.combine(start_date, start_time)
end_datetime = datetime.combine(end_date, end_time)

logger.info(f"Date range selected: {start_datetime} to {end_datetime}")

# Filter options
st.sidebar.header("Filter Options")

# Initialize sensor_ids with a default
sensor_ids = ["All"]

# Only try to get unique sensor IDs if we have data
if 'sensor_data' in st.session_state:
    if not st.session_state['sensor_data'].empty:
        if 'id' in st.session_state['sensor_data'].columns:
            sensor_ids = ["All"] + list(st.session_state['sensor_data']['id'].unique())

selected_sensor_id = st.sidebar.selectbox("Sensor ID", sensor_ids)
logger.info(f"Selected sensor ID: {selected_sensor_id}")

# Fetch data button
if st.sidebar.button("Fetch Data"):
    logger.info("Fetch Data button clicked")
    with st.spinner("Generating simulated data..."):
        try:
            if selected_sensor_id == "All":
                logger.info("Generating data for all sensors")
                sensor_data = fetch_sensor_data_in_range(start_datetime, end_datetime)
            else:
                logger.info(f"Generating data for sensor {selected_sensor_id}")
                sensor_data = fetch_sensor_data_in_range(start_datetime, end_datetime, selected_sensor_id)
            
            logger.info(f"Generated {len(sensor_data)} records")
            
            df = process_sensor_data(sensor_data)
            st.session_state['sensor_data'] = df
            st.session_state['last_refresh'] = datetime.now()
            
            # Reset simulation index when fetching new data
            if 'simulation_index' in st.session_state:
                st.session_state['simulation_index'] = 0
            
            # Clear real-time buffer when fetching new data
            if 'real_time_buffer' in st.session_state:
                del st.session_state['real_time_buffer']
            
            logger.info(f"Data processed and stored in session state. DataFrame shape: {df.shape}")
            
            # Success message
            st.success(f"Successfully generated {len(sensor_data)} data points for the selected range")
        except Exception as e:
            error_msg = f"Error during data generation: {str(e)}"
            logger.exception(error_msg)
            st.error(error_msg)

# Initialize session state for data
if 'sensor_data' not in st.session_state:
    logger.info("Initializing session state with initial data generation")
    
    with st.spinner("Generating initial data..."):
        try:
            sensor_data = fetch_all_sensor_data()
            logger.info(f"Generated {len(sensor_data)} records for initial load")
            
            df = process_sensor_data(sensor_data)
            st.session_state['sensor_data'] = df
            st.session_state['last_refresh'] = datetime.now()
            
            logger.info(f"Initial data processed and stored in session state. DataFrame shape: {df.shape}")
        except Exception as e:
            error_msg = f"Error during initial data generation: {str(e)}"
            logger.exception(error_msg)
            st.error(error_msg)
            # Create empty DataFrame on error to avoid errors later
            st.session_state['sensor_data'] = pd.DataFrame()
            st.session_state['last_refresh'] = datetime.now()

# Auto-refresh logic for batch data
if auto_refresh and not simulation_mode:
    logger.info("Auto-refresh is enabled")
    if 'last_refresh' in st.session_state:
        time_since_refresh = (datetime.now() - st.session_state['last_refresh']).total_seconds()
        logger.info(f"Time since last refresh: {time_since_refresh} seconds")
        
        if time_since_refresh > refresh_interval:
            logger.info("Auto-refreshing data")
            with st.spinner("Auto-refreshing data..."):
                try:
                    if selected_sensor_id == "All":
                        sensor_data = fetch_sensor_data_in_range(start_datetime, end_datetime)
                    else:
                        sensor_data = fetch_sensor_data_in_range(start_datetime, end_datetime, selected_sensor_id)
                    
                    df = process_sensor_data(sensor_data)
                    st.session_state['sensor_data'] = df
                    st.session_state['last_refresh'] = datetime.now()
                    
                    logger.info(f"Auto-refresh complete. DataFrame shape: {df.shape}")
                except Exception as e:
                    error_msg = f"Error during auto-refresh: {str(e)}"
                    logger.exception(error_msg)
                    st.error(error_msg)

# Real-time simulation logic
if simulation_mode and 'sensor_data' in st.session_state and not st.session_state['sensor_data'].empty:
    # Get current base data
    base_df = st.session_state['sensor_data']
    
    # Get next data point for simulation
    new_data_point = simulate_real_time_data(base_df, simulation_speed)
    
    if new_data_point is not None and not new_data_point.empty:
        # Update real-time buffer with new data point
        update_real_time_buffer(new_data_point)
        
        # Update timestamp for display
        st.session_state['last_refresh'] = datetime.now()
        
        # Use real-time buffer for visualization
        df = st.session_state['real_time_buffer']
        logger.info(f"Real-time simulation active. Buffer size: {len(df)}")
    else:
        df = base_df
else:
    # Get data from session state (normal mode)
    try:
        df = st.session_state['sensor_data']
        logger.info(f"Retrieved data from session state. DataFrame shape: {df.shape}")
    except Exception as e:
        error_msg = f"Error retrieving data from session state: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
        df = pd.DataFrame()

# Display last update time
if 'last_refresh' in st.session_state:
    refresh_time = st.session_state['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"Last refresh time: {refresh_time}")
    st.sidebar.markdown(f"Last updated: {refresh_time}")

# Simulation status indicator
if simulation_mode:
    simulation_status = st.empty()
    simulation_status.info(f"Real-time simulation mode active - {simulation_speed} points/second")

# Check if data exists
if df.empty:
    logger.warning("DataFrame is empty, showing warning")
    st.warning("No sensor data available. Click 'Fetch Data' to generate simulated data.")
else:
    logger.info(f"DataFrame has data. Shape: {df.shape}")
    
    # Display summary metrics
    st.markdown("## Power Metrics Summary")
    
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Readings", f"{len(df)}")
        
        if 'voltage' in df.columns:
            with col2:
                try:
                    avg_voltage = df['voltage'].mean()
                    st.metric("Average Voltage", f"{avg_voltage:.2f} V")
                    logger.info(f"Average voltage: {avg_voltage:.2f} V")
                except Exception as e:
                    logger.error(f"Error calculating average voltage: {str(e)}")
                    st.metric("Average Voltage", "Error")
        
        if 'current' in df.columns:
            with col3:
                try:
                    avg_current = df['current'].mean()
                    st.metric("Average Current", f"{avg_current:.2f} A")
                    logger.info(f"Average current: {avg_current:.2f} A")
                except Exception as e:
                    logger.error(f"Error calculating average current: {str(e)}")
                    st.metric("Average Current", "Error")
        
        if 'power' in df.columns:
            with col4:
                try:
                    avg_power = df['power'].mean()
                    st.metric("Average Power", f"{avg_power:.2f} W")
                    logger.info(f"Average power: {avg_power:.2f} W")
                except Exception as e:
                    logger.error(f"Error calculating average power: {str(e)}")
                    st.metric("Average Power", "Error")
        
        logger.info("Completed summary metrics section")
    except Exception as e:
        error_msg = f"Error in summary metrics section: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
    
    # Main visualizations
    st.markdown("## Data Visualizations")
    
    # Create placeholders for charts that will be updated in real-time mode
    voltage_chart = st.empty()
    current_chart = st.empty()
    power_chart = st.empty()
    scatter_chart = st.empty()
    
    # Row 1: Time Series of Voltage and Current
    try:
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.subheader("Voltage Over Time")
            
            if 'timestamp' in df.columns and 'voltage' in df.columns:
                try:
                    # Create line chart for voltage
                    fig = px.line(df, x='timestamp', y='voltage',
                                title="Voltage measurements over time",
                                labels={"timestamp": "Time", "voltage": "Voltage (V)"})
                    
                    fig.update_layout(height=400)
                    voltage_chart.plotly_chart(fig, use_container_width=True)
                    logger.info("Voltage chart created successfully")
                except Exception as e:
                    error_msg = f"Error creating voltage chart: {str(e)}"
                    logger.exception(error_msg)
                    st.error(error_msg)
            else:
                if 'timestamp' not in df.columns:
                    st.warning("Missing timestamp column for time series")
                if 'voltage' not in df.columns:
                    st.warning("Missing voltage column for voltage chart")
        
        with row1_col2:
            st.subheader("Current Over Time")
            
            if 'timestamp' in df.columns and 'current' in df.columns:
                try:
                    # Create line chart for current
                    fig = px.line(df, x='timestamp', y='current',
                                title="Current measurements over time",
                                labels={"timestamp": "Time", "current": "Current (A)"})
                    
                    fig.update_layout(height=400)
                    current_chart.plotly_chart(fig, use_container_width=True)
                    logger.info("Current chart created successfully")
                except Exception as e:
                    error_msg = f"Error creating current chart: {str(e)}"
                    logger.exception(error_msg)
                    st.error(error_msg)
            else:
                if 'timestamp' not in df.columns:
                    st.warning("Missing timestamp column for time series")
                if 'current' not in df.columns:
                    st.warning("Missing current column for current chart")
    except Exception as e:
        error_msg = f"Error in row 1 visualizations: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
    
    # Row 2: Power Analysis and Voltage-Current Relationship
    try:
        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            st.subheader("Power Consumption Over Time")
            
            if 'timestamp' in df.columns and 'power' in df.columns:
                try:
                    # Create area chart for power
                    fig = px.area(df, x='timestamp', y='power',
                                title="Power consumption over time",
                                labels={"timestamp": "Time", "power": "Power (W)"},
                                color_discrete_sequence=["rgba(0, 128, 0, 0.5)"])
                    
                    fig.update_layout(height=400)
                    power_chart.plotly_chart(fig, use_container_width=True)
                    logger.info("Power chart created successfully")
                except Exception as e:
                    error_msg = f"Error creating power chart: {str(e)}"
                    logger.exception(error_msg)
                    st.error(error_msg)
            else:
                if 'timestamp' not in df.columns:
                    st.warning("Missing timestamp column for time series")
                if 'power' not in df.columns:
                    st.warning("Missing power column for power chart")
        
        with row2_col2:
            st.subheader("Voltage vs Current Relationship")
            
            if 'voltage' in df.columns and 'current' in df.columns:
                try:
                    # Create scatter plot of voltage vs current
                    fig = px.scatter(df, x='voltage', y='current',
                                    title="Voltage vs Current",
                                    labels={"voltage": "Voltage (V)", "current": "Current (A)"},
                                    color='power' if 'power' in df.columns else None,
                                    color_continuous_scale='viridis')
                    
                    # Add trendline
                    fig.update_layout(height=400)
                    
                    # Only add best fit line if we have enough valid data points
                    valid_data = df.dropna(subset=['voltage', 'current'])
                    if len(valid_data) >= 2:  # Need at least 2 points for a line
                        try:
                            # Add a best fit line
                            poly_coeffs = np.polyfit(valid_data['voltage'], valid_data['current'], 1)
                            y_fit = np.poly1d(poly_coeffs)(df['voltage'])
                            
                            fig.add_trace(go.Scatter(
                                x=df['voltage'],
                                y=y_fit,
                                mode='lines',
                                name='Trend Line',
                                line=dict(color='red', dash='dash')
                            ))
                            logger.info("Added trendline to scatter plot successfully")
                        except Exception as e:
                            st.warning(f"Could not calculate trendline: {str(e)}")
                            logger.warning(f"Could not calculate trendline: {str(e)}")
                    
                    scatter_chart.plotly_chart(fig, use_container_width=True)
                    logger.info("Scatter plot created successfully")
                except Exception as e:
                    error_msg = f"Error creating scatter plot: {str(e)}"
                    logger.exception(error_msg)
                    st.error(error_msg)
            else:
                if 'voltage' not in df.columns:
                    st.warning("Missing voltage column for scatter plot")
                if 'current' not in df.columns:
                    st.warning("Missing current column for scatter plot")
    except Exception as e:
        error_msg = f"Error in row 2 visualizations: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)

    # Real-time simulation update loop
    if simulation_mode:
        # Add a real-time simulation indicator with timestamp
        st.markdown("---")
        st.markdown(f"**Real-time Simulation Active** - Last point added at {refresh_time}")
        
        # Add real-time statistics
        if 'real_time_buffer' in st.session_state:
            buffer_df = st.session_state['real_time_buffer']
            if not buffer_df.empty:
                st.markdown(f"**Simulation Stats:** {len(buffer_df)} points in buffer, "
                           f"Showing data from {buffer_df['timestamp'].min().strftime('%H:%M:%S')} "
                           f"to {buffer_df['timestamp'].max().strftime('%H:%M:%S')}")
        
        # Information about rerunning for simulation 
        st.info("The dashboard is simulating real-time data flow. Wait 1 second for the next update...")
        
        # Force a rerun after 1 second to simulate real-time updates
        time.sleep(1)
        st.experimental_rerun()

    # Footer with refresh information
    st.markdown("---")
    if auto_refresh and not simulation_mode:
        st.markdown(f"⚙️ Auto-refresh is enabled. Data will update every {refresh_interval} seconds.")
    elif not simulation_mode:
        st.markdown("⚙️ Auto-refresh is disabled. Click 'Fetch Data' in the sidebar to update.")

# Add debugging information in expandable section
with st.expander("Debug Information"):
    st.write("Dashboard Version: 1.0.3 (with simulated data)")
    
    st.write("Date range:")
    st.json({
        "start_datetime": start_datetime.isoformat(),
        "end_datetime": end_datetime.isoformat()
    })
    
    if 'df' in locals():
        st.write("Data Shape:", df.shape)
        
        # Show column names
        st.write("Column names:", df.columns.tolist())
        
        # Check for key columns
        st.write("Key columns present:", {
            "timestamp": "timestamp" in df.columns,
            "voltage": "voltage" in df.columns,
            "current": "current" in df.columns,
            "power": "power" in df.columns,
            "id": "id" in df.columns
        })
        
        # Show the data types
        st.write("Data Types:")
        for col, dtype in df.dtypes.items():
            st.write(f"{col}: {dtype}")
        
        # Display sample data
        if not df.empty:
            st.write("Sample Data (First 5 rows):")
            st.dataframe(df.head())
            
            # Check for any NaN values
            st.write("NaN value counts:")
            st.write(df.isna().sum())
        else:
            st.write("DataFrame is empty")
    else:
        st.write("DataFrame not available in local scope")
    
    # Show session state contents
    st.write("Session state keys:", list(st.session_state.keys()))
    
    # Simulation stats if available
    if simulation_mode:
        st.write("Simulation Mode Stats:")
        st.write(f"Simulation Index: {st.session_state.get('simulation_index', 'Not set')}")
        st.write(f"Buffer Size: {len(st.session_state.get('real_time_buffer', pd.DataFrame())) if 'real_time_buffer' in st.session_state else 'No buffer'}")