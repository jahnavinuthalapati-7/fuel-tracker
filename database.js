const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const db = new sqlite3.Database(path.join(__dirname, 'fuel_tracker.db'));

db.serialize(() => {
  // Users table
  db.run(` 
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      role TEXT DEFAULT 'User',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Fuel entries table - COMPLETE SCHEMA
  db.run(`
    CREATE TABLE IF NOT EXISTS fuel_entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      slip_no TEXT UNIQUE NOT NULL,
      transaction_type TEXT NOT NULL,
      fuel_type TEXT NOT NULL,
      date DATE NOT NULL,
      quantity REAL,
      rate REAL,
      amount REAL,
      vendor_name TEXT,
      vendor_location TEXT,
      vehicle_no TEXT,
      vin_no TEXT,
      registration_no TEXT,
      model_no TEXT,
      allocated_to TEXT,
      opening_odometer REAL,
      closing_odometer REAL,
      km_run REAL,
      issue_quantity REAL,
      mileage REAL,
      opening_stock REAL,
      purchase_qty REAL,
      issue_qty REAL,
      closing_stock REAL,
      physical_stock REAL,
      variance REAL,
      recipient_name TEXT,
      receiver_name TEXT,
      approved_by TEXT,
      recorded_by TEXT,
      remarks TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  console.log(' Database tables ready');
});

module.exports = db;
