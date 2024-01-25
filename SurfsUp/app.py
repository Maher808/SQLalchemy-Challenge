# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from datetime import date
import numpy as np


#################################################
# Database Setup
#################################################

# Create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """Homepage with available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation: Precipitation data for the last 12 months<br/>"
        f"/api/v1.0/stations: List of stations<br/>"
        f"/api/v1.0/tobs: Temperature observations for the most active station in the last year<br/>"
        f"/api/v1.0/start_date: Minimum, Average, and Maximum temperatures from the start date to the most recent date<br/>"
        f"/api/v1.0/start_date/end_date: Minimum, Average, and Maximum temperatures for the specified date range<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last 12 months."""
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    stations_data = session.query(Station.station).all()
    stations_list = [station for (station,) in stations_data]
    return jsonify(stations_list)


@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station in the last year."""
    most_active_station = session.query(Measurement.station, func.count(Measurement.station).label('station_count')).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()
    most_active_station_id = most_active_station[0]
    most_recent_date_most_active = session.query(func.max(Measurement.date)).\
        filter(Measurement.station == most_active_station_id).scalar()
    one_year_ago_most_active = dt.datetime.strptime(most_recent_date_most_active, '%Y-%m-%d') - dt.timedelta(days=365)
    temperature_data_most_active = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station_id,
               Measurement.date >= one_year_ago_most_active).all()

    temperature_list_most_active = [{"date": date, "temperature": tobs} for date, tobs in temperature_data_most_active]
    
    return jsonify(temperature_list_most_active)


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_start_end(start=None, end=None):
    """Return TMIN, TAVG, and TMAX for all dates greater than or equal to the start date."""
    temperature_stats = [
        func.min(Measurement.tobs).label('min_temperature'),
        func.avg(Measurement.tobs).label('avg_temperature'),
        func.max(Measurement.tobs).label('max_temperature')
    ]

    if not end:

        start = dt.datetime.strptime(start, "%Y-%m-%d")
        output = session.query(*temperature_stats).\
        filter(Measurement.date >= start).all()
        tempstats = list(np.ravel(output))
        return jsonify(tempstats)
    
    # calculate stats with start and end:
    start = dt.datetime.strptime(start, "%Y-%m-%d")
    end = dt.datetime.strptime(end, "%Y-%m-%d")

    output = session.query(*temperature_stats).\
    filter(Measurement.date >= start).\
    filter(Measurement.date <= end).all()

    # Close the session after data retrieval
    session.close()

    # output to 1D array and convert to a list
    tempstats = list(np.ravel(output))
    return jsonify(tempstats)

if __name__ == '__main__':
    app.run(debug=True)