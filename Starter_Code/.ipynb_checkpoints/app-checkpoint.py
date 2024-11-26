from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import datetime as dt

# Set up the database
db_path = "hawaii.sqlite"
engine = create_engine(f"sqlite:///{db_path}")

# Reflect the database into a new model
Base = automap_base()
Base.prepare(autoload_with=engine)

# Map tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create Flask app
app = Flask(__name__)

@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data."""
    session = Session(engine)
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date_dt = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_before = most_recent_date_dt - dt.timedelta(days=365)
    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_before).all()
    session.close()
    
    # Convert to dictionary
    precipitation_data = {date: prcp for date, prcp in results}
    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations."""
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()
    
    # Convert list of tuples into a list
    stations = [result[0] for result in results]
    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station for the last year."""
    session = Session(engine)
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date_dt = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_before = most_recent_date_dt - dt.timedelta(days=365)
    
    # Query the most active station
    active_station = session.query(Measurement.station, func.count(Measurement.id))\
                            .group_by(Measurement.station)\
                            .order_by(func.count(Measurement.id).desc()).first()[0]
    
    results = session.query(Measurement.tobs).filter(Measurement.station == active_station)\
                                              .filter(Measurement.date >= one_year_before).all()
    session.close()
    
    # Convert to list
    tobs_list = [result[0] for result in results]
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_range(start=None, end=None):
    """Return min, avg, and max temperatures for a given start or start-end range."""
    session = Session(engine)
    if not end:
        # Calculate for all dates greater than or equal to the start date
        results = session.query(func.min(Measurement.tobs), 
                                func.avg(Measurement.tobs), 
                                func.max(Measurement.tobs)).filter(Measurement.date >= start).all()
    else:
        # Calculate for the date range
        results = session.query(func.min(Measurement.tobs), 
                                func.avg(Measurement.tobs), 
                                func.max(Measurement.tobs)).filter(Measurement.date >= start)\
                                                           .filter(Measurement.date <= end).all()
    session.close()
    
    # Convert to dictionary
    temp_data = {
        "start_date": start,
        "end_date": end if end else "N/A",
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }
    return jsonify(temp_data)

if __name__ == "__main__":
    app.run(debug=True)
