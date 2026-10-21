-- 0002_trip_departure_date: optional ISO YYYY-MM-DD departure date on non-template trips.

ALTER TABLE trips ADD COLUMN departure_date TEXT CHECK (
    departure_date IS NULL OR (
        length(departure_date) = 10
        AND departure_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    )
);
