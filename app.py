from shiny import App, ui, render, reactive
from ipyleaflet import Map, Marker
from shinywidgets import output_widget, render_widget  
from ipywidgets import Layout
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
import matplotlib.pyplot as plt
from prophet import Prophet
from datetime import timedelta

import matplotlib.dates as mdates
df = pd.read_csv('data/cities.csv')
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

cities = df['city_state'].unique().tolist()

# Define the UI layout
app_ui = ui.page_sidebar( 
    ui.sidebar(ui.input_selectize(
            "city", "City", cities, selected="Urbana, Illinois"
        ),ui.output_text("get_coordinates"),
        ui.input_date_range("daterange", "Dates", start="2022-01-01", 
                end="2024-01-01",
                min="2020-01-01", 
                max="2024-01-01"), 
        ui.input_numeric("numeric", "Numeric input", 1, min=1, max=5),ui.input_radio_buttons(  
        "radio_trend",  
        "Forecast Trend",  
        {"1": "Flat", "2": "Linear"}, selected="1" ), ui.input_radio_buttons(  
        "radio_units",  
        "Units",  
        {"1": "Farenheit", "2": "Celsius"}, selected="1" ), 
        ui.output_ui("temp_slider"),
         ui.input_checkbox_group(  
        "checkbox_options",  
        "Plot Options",  
        {  
            "a": "Weekly Rolling Average",  
            "b": "Monthly Rolling Average",  
    
        },  
    ),    
     ui.output_ui("table_slider"), 
     output_widget("map"), 
      

          bg="#f8f8f8",
        open="always",width=334,
 
    
),
ui.page_navbar(  
    ui.nav_panel("Historical", ui.div(
      ui.output_plot("weather_plot"),
       ui.output_data_frame("temp_table"),
        # ui.output_plot("weather_plot"), ui.output_data_frame("temp_table"), 
    ),),  
    ui.nav_panel( "Forecast",  ui.div(
        ui.output_plot("forecast_plot"), ui.output_data_frame("forecast_table"), 
    ),),  
    ui.nav_panel("About", ui.markdown("""

# About the Heat Pump Efficiency Dashboard

This interactive dashboard offers a comprehensive tool for evaluating the potential benefits of installing heat pumps in homes across the United States. By integrating historical weather data with the performance characteristics of heat pumps, the dashboard empowers users to make data-driven decisions on their heating and cooling solutions.

## Understanding Heat Pumps

Heat pumps are a **sustainable alternative** to traditional heating and cooling systems. Utilizing a refrigerant, heat pumps transfer heat from the outdoors into your home during winter and vice versa during summer. This technology not only reduces carbon emissions but also offers significant savings on energy bills due to its high efficiency.

## Data Sources and Methodology

- **Location Data:** Utilizing data from [SimpleMaps](https://simplemaps.com/data/us-cities), users can accurately select their city, ensuring the weather data retrieved is as relevant as possible.
- **Weather Data:** Our dashboard fetches historical weather data from [Open-Meteo](https://open-meteo.com), focusing on daily minimum temperatures to assess the cold days' impact on heat pump efficiency.

## How to Use the Dashboard

1. **Select Your Location:** Choose your city from the dropdown list. The dashboard will display the corresponding weather station data, including coordinates.
2. **Define the Date Range:** Pick a start and end date to collect historical temperature data. This selection will frame the period analyzed for heat pump performance.
3. **Temperature Units and Threshold:** Customize the dashboard to show temperatures in either Fahrenheit or Celsius. Use the slider to set a temperature threshold, highlighting the performance of heat pumps under specific conditions.
4. **Interpreting the Data:** The dashboard visualizes the temperature data in a plot and summarizes the analysis in a table, showing the proportion of days below the chosen temperature threshold.

## Why Heat Pumps?

- **Energy Efficiency:** Heat pumps can provide equivalent space conditioning at as little as one-quarter of the cost of operating conventional heating or cooling appliances.
- **Environmental Impact:** By transferring heat rather than generating it, heat pumps reduce carbon emissions, making them an eco-friendly choice for your home.
- **Versatility:** Heat pumps offer a dual function, providing heating in the winter and cooling in the summer, thus offering year-round climate control.

## Making Informed Decisions

The decision to install a heat pump should be informed by an understanding of its performance in your specific climate. This dashboard provides you with tangible data on how heat pumps might perform during the coldest days in your region, allowing for a more informed investment in your home’s heating and cooling system.

Remember, while this tool offers valuable insights, it's essential to consider all aspects of heat pump installation, including initial costs, maintenance, and the specific needs of your home. Consulting with a professional can further tailor the decision to your circumstances.

""")),  
     
    id="page",  
)  , 
    

    title="Daily Heat Pump Efficiency Counter",  
    id="page",  
)  

# main function to be executed
def server(input, output, session):
    weather_data = reactive.Value(pd.DataFrame())
    future_data = reactive.Value(pd.DataFrame())
    error_message = reactive.Value(None)
    plot_allowed=reactive.Value(True)

    @reactive.Effect
    def call_api_on_user_input():

        if input.daterange() is not None:
            start_date, end_date = input.daterange()
            if end_date < start_date + timedelta(days=365):
                plot_allowed.set(False)
            else:
                plot_allowed.set(True)

            formatted_start_date = start_date.strftime("%Y-%m-%d")
            formatted_end_date=end_date.strftime("%Y-%m-%d")
            

            selected_row = df[df['city_state'] == input.city()]
            lat=selected_row['lat'].values[0]
            lon=selected_row['lng'].values[0]
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": formatted_start_date,
                "end_date": formatted_end_date,
                "daily": "temperature_2m_min",
                "temperature_unit": "fahrenheit" if input.radio_units() == "1" else "celsius"
            }
        
        # api_response = requests.get("https://api.open-meteo.com/v1/forecast", params=params)
        try:
            responses = openmeteo.weather_api(url, params=params)
            error_message.set(None)
            response = responses[0]
            latitude=response.Latitude()
            longitude=response.Longitude()
            

            daily = response.Daily()
            daily_temperature_2m_min = daily.Variables(0).ValuesAsNumpy()

            daily_data = {"date": pd.date_range(
                start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
                end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
                freq = pd.Timedelta(seconds = daily.Interval()),
                inclusive = "left"
            )}
            daily_data["temperature_2m_min"] = daily_temperature_2m_min
            daily_data["longitude"] = longitude
            daily_data["latitude"] = latitude
            daily_dataframe = pd.DataFrame(data = daily_data)
            weather_data.set(daily_dataframe)
            # Process the response...
        except Exception as e:
            # Here you could set the error message in a reactive value if needed
            error_message.set(str(e)) 
            


    @render.text
    def get_coordinates():
        if error_message.get():
            raise Exception(error_message.get()) 
        else:
            df_weather = weather_data.get()
            return f"{df_weather['latitude'].values[0]:.4f}°N, {df_weather['longitude'].values[0]:.4f}°E"
        
 
    @render.ui
    def temp_slider():
        if input.radio_units() == "1":
            # Settings for Fahrenheit
            min_val, max_val, default_val = -15, 50, 5
        else:
            # Settings for Celsius (assuming conversion or different desired range)
            min_val, max_val, default_val = -25, 10, -15  # Example conversion
            
        # Dynamically update the slider in the UI
        return ui.input_slider("slider", "Temperature Threshold", min_val, max_val, default_val)
    

    @render.ui
    def table_slider():
        if input.radio_units() == "1":
            # Settings for Fahrenheit
            min_val, max_val, default_min_val, default_max_val = -25, 60, 0, 15
        else:
            # Settings for Celsius (assuming conversion or different desired range)
            min_val, max_val, default_min_val, default_max_val = -30, 15, -20, -10  # Example conversion
            
        # Dynamically update the slider in the UI
        
        return ui.input_slider("table_slider", "Table Temperatures", min_val, max_val, value=[default_min_val,default_max_val])
    
    @render_widget  
    def map():
        df_weather = weather_data.get()
        map_layout = Layout(width='297', height='200px')  #
        map= Map(center=(df_weather['latitude'].values[0], df_weather['longitude'].values[0]), zoom=12,layout=map_layout) 
        point = Marker(location=(df_weather['latitude'].values[0], df_weather['longitude'].values[0]), draggable=True)  
        map.add_layer(point)  
        return map
    
    
    @render.plot
    def weather_plot():
        if error_message.get():
            raise Exception(error_message.get())  
        else:
            df_weather = weather_data.get()
            if df_weather is not None:
                fig, ax = plt.subplots(figsize=(10, 5))
                # Convert the dates to matplotlib's internal format
                spec_value=input.slider()
                marker_size = 10  # Adjust the size of markers as needed
                marker_color = 'black' 
                # for _, row in df_weather.iterrows():
                #     color = 'black' if row['temperature_2m_min'] >= spec_value else 'grey'
                #     ax.scatter(row['date'], row['temperature_2m_min'], color=color, alpha=1.0, s=marker_size)

                above_df = df_weather[df_weather['temperature_2m_min'] >= spec_value]
                below_df = df_weather[df_weather['temperature_2m_min'] < spec_value]

                # Plotting points above or equal to the specific value in black
                ax.scatter(above_df['date'], above_df['temperature_2m_min'], color='black',s=marker_size)

                # Plotting points below the specific value in grey with alpha transparency
                ax.scatter(below_df['date'], below_df['temperature_2m_min'], color='lightgrey', alpha=1.0, s=marker_size)
                if 'a' in input.checkbox_options():  # Assuming 'a' is the value for the weekly rolling average checkbox
                    # Calculate the rolling average with a 7-day window
                    rolling_avg = df_weather['temperature_2m_min'].rolling(window=7).mean()

                    # Plot the rolling average
                    ax.plot(df_weather['date'], rolling_avg, color='orange', label='Weekly Rolling Average')
                if 'b' in input.checkbox_options():  # Assuming 'a' is the value for the weekly rolling average checkbox
                    # Calculate the rolling average with a 7-day window
                    rolling_avg_month = df_weather['temperature_2m_min'].rolling(window=30).mean()

                    # Plot the rolling average
                    ax.plot(df_weather['date'], rolling_avg_month, color='blue', label='Monthly Rolling Average')

                plt.tight_layout()
                ax.grid(True, color="#d3d3d3", alpha=0.7)

                ax.set_xlim(df_weather['date'].min() - pd.Timedelta(days=90), df_weather['date'].max() + pd.Timedelta(days=90))
                ax.set_ylim(df_weather['temperature_2m_min'].min()-2, df_weather['temperature_2m_min'].max() + 15)          
                temp_unit = "°C" if input.radio_units() == "2" else "°F"
                ax.set_ylabel(f'Daily Minimum Temperature ({temp_unit})')
                
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.tick_params(axis='x', which='major', labelsize=8)
                ax.axhline(y=spec_value, color='grey', linestyle='-', label='Freezing Point',alpha=0.8, linewidth=0.7) 
                fig.tight_layout()
                return fig

    @render.data_frame()
    def temp_table():
        if error_message.get():
            raise Exception(error_message.get()) 
        else:
            df_weather = weather_data.get()
            if df_weather is not None:
                temp_range=input.table_slider()
                min_temp, max_temp = temp_range[0], temp_range[1]
                total_days = len(df_weather)
                rows = []
                for temp in range(min_temp, max_temp + 1):
                    df_at_temp = df_weather[df_weather['temperature_2m_min'] < temp]
                    days_at_temp = len(df_at_temp)
                    proportion_at_temp = days_at_temp / total_days if total_days > 0 else 0
                    
                    # Append a dictionary for each temperature's data
                    rows.append({
                        "Temp": temp,
                        "Days Below": days_at_temp,
                        "Proportion Below": f"{proportion_at_temp:.3f}".rstrip('0').rstrip('.')
                    })

            detailed_df = pd.DataFrame(rows)
            detailed_df = detailed_df.sort_values(by="Temp", ascending=False)
            
            return render.DataGrid(detailed_df,summary=False,width='100%', row_selection_mode='multiple', height='fit-content')
    
    @render.plot
    def forecast_plot():
        if error_message.get():
            raise Exception(error_message.get())
        else:
            if plot_allowed.get()== True:
                growth=input.radio_trend()
                growth="linear" if growth=="2" else "flat"
                years=input.numeric()
                spec_value=input.slider()
                df_weather = weather_data.get()
                if df_weather is not None:
                    fig, ax = plt.subplots()
                    df_prophet= df_weather.rename(columns={"date": "ds", "temperature_2m_min": "y"})
                    df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)
                    model = Prophet(growth=growth, interval_width=0.95)
                    model.fit(df_prophet)
                    future = model.make_future_dataframe(periods=365*years)
                    forecast = model.predict(future)
                    marker_size = 10 
                    plt.scatter(df_prophet['ds'], df_prophet['y'], color='black', label='Historical Data', s=marker_size)
                    forecast_future = forecast[forecast['ds'] > df_prophet['ds'].max()]
                    fig = model.plot(forecast_future, ax=plt.gca(),)
                    temp_unit = "°C" if input.radio_units() == "2" else "°F"
                    ax.set_ylabel(f'Daily Minimum Temperature ({temp_unit})')
                    ax.axhline(y=spec_value, color='grey', linestyle='-', label='Freezing Point',alpha=0.8, linewidth=0.7)
                    fig.gca().set_xlabel('') 
                    fig.tight_layout()
                    future_data.set(forecast_future)
                    return fig
            else:
                fig, ax = plt.subplots()
                ax.axis('off')
                return fig
    
    @render.data_frame()
    def forecast_table():
        if error_message.get():
            raise Exception(error_message.get())
        else:
            if plot_allowed.get()== True:
                df_weather = future_data.get()
                if df_weather is not None:
                    temp_range=input.table_slider()
                    min_temp, max_temp = temp_range[0], temp_range[1]
                    total_days = len(df_weather)
                    rows = []
                    for temp in range(min_temp, max_temp + 1):
                        days_below = df_weather[df_weather['yhat_lower'] < temp]
                        number_of_days_below = len(days_below)
                        proportion_below = number_of_days_below / total_days if total_days > 0 else 0
                        
                        # Append a dictionary for each temperature's data
                        rows.append({
                            "Temp": temp,
                            "Days Below": number_of_days_below,
                            "Proportion Below": f"{proportion_below:.3f}".rstrip('0').rstrip('.')
                        })

                detailed_df = pd.DataFrame(rows)
                detailed_df = detailed_df.sort_values(by="Temp", ascending=False)
                
                return render.DataGrid(detailed_df,summary=False,width='100%', row_selection_mode='multiple', height='fit-content')
            else:
                return None
    

    
    


app = App(app_ui, server)

