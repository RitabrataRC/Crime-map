from flask import Flask, render_template, request, redirect, url_for
import json
import pandas as pd
import plotly.express as px
import math
from flask_ngrok import run_with_ngrok

app = Flask(__name__)

#run_with_ngrok(app)

def add_tel_data(df, year):
    if year < 2014:
        average = math.ceil(df['crime'].nsmallest(5).mean())
        tel_data = {'state': 'Telangana', 'district': 'total', 'year': year, 'crime': average}
        df = df._append(tel_data, ignore_index=True)
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    data = pd.read_csv('C:/Users/KIIT/Desktop/My project/Crime/crime_data/crime_data.csv')
    years = sorted(data['year'].unique())
    crimes = sorted(data.columns[3:].tolist())
    selected_year = 2008
    selected_crime = 'total'

    if request.method == 'POST':
        selected_year = int(request.form.get('year', selected_year))
        selected_crime = request.form.get('crime', selected_crime)
        if 'see_more' in request.form:
            return redirect(url_for('show', year=selected_year, crime=selected_crime))

    state_data = data[(data['district'] == 'total') & (data['year'] == selected_year)][['state', 'district', 'year', selected_crime]]
    state_data.rename(columns={selected_crime: 'crime'}, inplace=True)
    state_data = add_tel_data(state_data, selected_year)

    detailed_data = {}
    for state in state_data['state'].unique():
        state_crime_data = data[(data['state'] == state) & (data['year'] == selected_year)]
        detailed_data[state] = {'crime_data': state_crime_data.to_dict(orient='list')}

    with open("C:/Users/KIIT/Desktop/My project/Crime/states_india.geojson", 'r') as f:
        india = json.load(f)

    state_id_map = {}
    for feature in india["features"]:
        feature["id"] = feature["properties"]["state_code"]
        state_id_map[feature["properties"]["st_nm"]] = feature["id"]

    state_data["id"] = state_data["state"].apply(lambda x: state_id_map.get(x, x))

    fig = px.choropleth(
        state_data,
        locations="id",
        geojson=india,
        color="crime",
        hover_name="state",
        hover_data=["crime"],
        title="Crime in India",
        color_continuous_scale=px.colors.sequential.Reds,
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False
    )

    fig.update_layout(
        dragmode="zoom",  # Enables zoom and drag functionality
        geo=dict(
            projection_scale=4  # Keep it at 1 for default scaling, allowing user control
        ),
        width=950,
        height=700
    )

    graph_html = fig.to_html(full_html=False)

    return render_template('index.html', plot_div=graph_html, years=years, crimes=crimes, selected_year=selected_year, selected_crime=selected_crime, detailed_data=json.dumps(detailed_data))


@app.route('/main', methods=['GET', 'POST'])
def show():
    st_data = pd.read_csv('district_crime.csv')
    states = sorted(list(set(st_data['state'])))

    selected_state = request.form.get('state')

    # Set the default state to states[38] if no state is selected
    if selected_state is None:
        selected_state = states[38]

    selected_crime = request.args.get('crime')
    selected_year = request.args.get('year')

    state_data = st_data[st_data['state'] == selected_state]
    year_data = state_data[state_data['year'] == int(selected_year)]

    # Line graph: Crime trend over the years in the selected state
    df = state_data[state_data['district'] == 'total']
    line_fig = px.line(df, x='year', y=selected_crime, title=f'{selected_crime} Trend in {selected_state}')
    line_graph = line_fig.to_html(full_html=False)

    # Bar graph: Crime distribution in different districts of the selected state for the selected year
    df = year_data[year_data['district'] != 'total']
    district_crime_fig = px.bar(df, x='district', y=selected_crime,
                                title=f'{selected_crime} in Different Districts of {selected_state} for {selected_year}')
    district_crime_graph = district_crime_fig.to_html(full_html=False)

    return render_template(
        'main.html',
        states=states,
        selected_state=selected_state,
        selected_crime=selected_crime,
        selected_year=selected_year,
        line_graph=line_graph,
        district_crime_graph=district_crime_graph
    )


if __name__ == '__main__':
    app.run(debug=True)
    #app.run()
