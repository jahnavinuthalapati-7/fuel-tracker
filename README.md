# Fuel Tracker 


```bash
npm install
npm start
```

**First Time Setup:**
1. Visit: `http://localhost:4000/api/check-setup`
2. Then go to: `http://localhost:4000`



## Features

 **Dashboard** - Real-time stock tracking with Old Stock, Purchased, Allocated, and TOTAL
 **Fuel Entry** - Separate tabs for Purchase and Issue transactions
 **Purchase Form** - Slip No, Fuel Type, Initial Stock, Qty, Rate, Amount (AUTO), Vendor, Approved By, Remarks
 **Issue Form** - Slip No, Vehicle Info, Odometer fields, KM Run (AUTO), Issue Qty, Mileage (AUTO), Approvals
 **Auto-Calculations** - Amount, KM Run, Mileage, Closing Stock all calculated automatically
 **Reports** - Complete table with all columns and filters
 **Export** - Excel (.xlsx), PDF (.pdf), Word (.docx)
 **Search** - Dashboard search by Slip No, Vehicle, Fuel Type, Allocated To, Approved By
 **User Management** - Create, list, and delete users
 **Password Change** - Secure password update
 **Stock Calculation** - Old Stock SEPARATE from Purchases, proper tracking

## Database

Uses SQLite. Database file: `fuel_tracker.db`

## API Endpoints

- `POST /api/login` - Login
- `GET /api/check-setup` - Create admin user (first time only)
- `POST /api/fuel-entry` - Create fuel entry
- `GET /api/fuel-entries` - Get all entries (with search/filter)
- `DELETE /api/fuel-entry/:id` - Delete entry
- `GET /api/dashboard` - Get dashboard stats
- `GET /api/export/excel` - Export to Excel
- `GET /api/export/pdf` - Export to PDF
- `GET /api/export/word` - Export to Word
- `GET /api/users` - Get all users
- `POST /api/users` - Create user
- `DELETE /api/users/:id` - Delete user
- `POST /api/change-password` - Change password


